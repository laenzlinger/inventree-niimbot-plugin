"""Niimbot label printing plugin for InvenTree.

Supports direct printing of labels to USB or Bluetooth label printers, using NiimbotPrintX.
"""

# translation
from django.utils.translation import gettext_lazy as _

# printing options
from rest_framework import serializers

from django.db import models
from django.utils.translation import gettext_lazy as _

from . import NIIMBOT_PLUGIN_VERSION

# InvenTree plugin libs
from report.models import LabelTemplate
from plugin import InvenTreePlugin
from plugin.machine import BaseMachineType
from plugin.machine.machine_types import LabelPrinterBaseDriver, LabelPrinterMachine

# Image library
from PIL import Image

import asyncio

# NiimbotPrintX printer client
from inventree_niimbot.nimmy.printer import PrinterClient, InfoEnum
from inventree_niimbot.nimmy.logger_config import setup_logger, get_logger, logger_enable


class NiimbotLabelSerializer(serializers.Serializer):
    """Custom serializer class for NiimbotLabelPlugin.

    Used to specify printing parameters at runtime
    """

    copies = serializers.IntegerField(
        default=1,
        label=_("Copies"),
        help_text=_("Number of copies to print"),
    )

# Backwards compatibility imports
try:
    from plugin.mixins import MachineDriverMixin
except ImportError:
    class MachineDriverMixin:
        """Dummy mixin for backwards compatibility."""

        pass

class NiimbotLabelPlugin(MachineDriverMixin, InvenTreePlugin):

    AUTHOR = "piramja"
    DESCRIPTION = "Label printing plugin for Niimbot label printers"
    VERSION = NIIMBOT_PLUGIN_VERSION

    MIN_VERSION = "0.16.0"

    NAME = "Niimbot Labels"
    SLUG = "niimbot"
    TITLE = "Niimbot Label Printer"

    PrintingOptionsSerializer = NiimbotLabelSerializer

    # Use background printing
    BLOCKING_PRINT = False

    def get_machine_drivers(self) -> list:
        """Register machine drivers."""
        return [NiimbotLabelPrinterDriver]


class NiimbotLabelPrinterDriver(LabelPrinterBaseDriver):
    """Niimbot label printing driver for InvenTree."""

    SLUG = "niimbot"
    NAME = "Niimbot Label Printer Driver"
    DESCRIPTION = "Niimbot label printing driver for InvenTree"

    def __init__(self, *args, **kwargs):
        """Initialize the NiimbotLabelPrinterDriver."""

        self.MACHINE_SETTINGS = {
            "CONNECTION": {
                "name": _("Connection Type"),
                "description": _("USB serial or Bluetooth"),
                "choices": [
                    ("usb", "USB Serial"),
                    ("bluetooth", "Bluetooth"),
                ],
                "default": "usb",
                "required": True,
            },
            "USB_PORT": {
                "name": _("USB Port"),
                "description": _("Serial device path"),
                "choices": [
                    ("/dev/niimbot", "/dev/niimbot"),
                    ("/dev/ttyUSB0", "/dev/ttyUSB0"),
                    ("/dev/ttyACM0", "/dev/ttyACM0"),
                ],
                "default": "/dev/niimbot",
                "required": False,
            },
            "MODEL": {
                "name": _("Printer Model"),
                "description": _("Select model of Niimbot printer"),
                "choices": [
                    ("b1", "Niimbot B1"),
                    ("b18", "Niimbot B18"),
                    ("b21", "Niimbot B21"),
                    ("d11", "Niimbot D11"),
                    ("d110", "Niimbot D110")
                ],
                "default": "d110",
                "required": True,
            },
            "DENSITY": {
                "name": _("Density"),
                "description": _("Density of the print (3 is max for b18, d11, d110)"),
                "choices": [
                    ("1", "density 1"),
                    ("2", "density 2"),
                    ("3", "density 3"),
                    ("4", "density 4"),
                    ("5", "density 5"),
                ],
                "default": "3",
                "required": True,
            },
            "ROTATION": {
                "name": _("Rotation"),
                "description": _("Image rotation (clockwise)"),
                "choices": [
                    ("0", "0 degrees"),
                    ("90", "90 degrees"),
                    ("180", "180 degrees"),
                    ("270", "270 degrees"),
                ],
                "default": "0",
                "required": True,
            },
            "SCALING": {
                "name": _("Scaling (%)"),
                "description": _("Image scaling in percent"),
                "choices": [
                    ("2", "200%"),
                    ("1.5", "150%"),
                    ("1", "100%"),
                    ("0.75", "75%"),
                    ("0.5", "50%"),
                ],
                "default": "1",
                "required": True,
            },
            "V_OFFSET": {
                "name": _("Vertical Offset (px)"),
                "description": _("Image offset vertical"),
                "default": "0",
                "required": False,
            },
            "H_OFFSET": {
                "name": _("Horizontal Offset (px)"),
                "description": _("Image offset horizontal"),
                "default": "0",
                "required": False,
            },
        }

        super().__init__(*args, **kwargs)


    def init_machine(self, machine: BaseMachineType):
        """Machine initialize hook."""
        machine.set_status(LabelPrinterMachine.MACHINE_STATUS.CONNECTED)


    def print_label(self, machine: LabelPrinterMachine, label: LabelTemplate, item, **kwargs) -> None:
        """Send the label to the printer."""

        options = kwargs.get("printing_options", {})
        n_copies = int(options.get("copies", 1))

        label_image = self.render_to_png(label, item)

        # Read settings
        connection = machine.get_setting("CONNECTION", "D")
        model = machine.get_setting("MODEL", "D")
        density = int(machine.get_setting("DENSITY", "D"))
        vertical_offset = int(machine.get_setting("V_OFFSET", "D") or 0)
        horizontal_offset = int(machine.get_setting("H_OFFSET", "D") or 0)
        scaling = float(machine.get_setting("SCALING", "D"))
        rotation = int(machine.get_setting("ROTATION", "D")) + 90
        rotation = rotation % 360

        # Rotate image
        if rotation in [90, 180, 270]:
            label_image = label_image.rotate(rotation, expand=True)

        # Resize image
        width, height = label_image.size
        new_size = (int(width * scaling), int(height * scaling))
        label_image = label_image.resize(new_size, Image.LANCZOS)

        # Add offsets to the image data directly if model is b1
        if model == "b1":
            if vertical_offset > 0 or horizontal_offset > 0:
                new_image = Image.new("RGB", (label_image.width + horizontal_offset, label_image.height + vertical_offset), (255, 255, 255))
                new_image.paste(label_image, (horizontal_offset, vertical_offset))
                label_image = new_image

        # Print labels
        if connection == "usb":
            usb_port = machine.get_setting("USB_PORT", "D") or "/dev/niimbot"
            asyncio.run(self._print_serial(usb_port, model, density, label_image, n_copies, vertical_offset, horizontal_offset))
        else:
            asyncio.run(self._print_ble(model, density, label_image, n_copies, vertical_offset, horizontal_offset))


    async def _print_serial(self, port, model, density, image, quantity, vertical_offset, horizontal_offset):
        from inventree_niimbot.nimmy.serial_transport import SerialTransport
        transport = SerialTransport(port)
        printer = PrinterClient(device=port, transport=transport)
        if await printer.connect():
            if model == "b1":
                await printer.print_imageV2(image, density=density, quantity=quantity)
            else:
                await printer.print_image(image, density=density, quantity=quantity, vertical_offset=vertical_offset, horizontal_offset=horizontal_offset)
            await printer.disconnect()


    async def _print_ble(self, model, density, image, quantity, vertical_offset, horizontal_offset):
        from inventree_niimbot.nimmy.bluetooth import find_device
        device = await find_device(model)
        printer = PrinterClient(device)
        if await printer.connect():
            if model == "b1":
                await printer.print_imageV2(image, density=density, quantity=quantity)
            else:
                await printer.print_image(image, density=density, quantity=quantity, vertical_offset=vertical_offset, horizontal_offset=horizontal_offset)
            await printer.disconnect()
