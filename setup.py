# -*- coding: utf-8 -*-

import importlib
import importlib.util
import os
import setuptools

"""Read the plugin version from the source code."""
module_path = os.path.join(
    os.path.dirname(__file__), "inventree_niimbot", "__init__.py"
)
spec = importlib.util.spec_from_file_location("inventree_niimbot", module_path)
inventree_niimbot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventree_niimbot)

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()


setuptools.setup(
    name="inventree-niimbot-plugin",

    version=inventree_niimbot.NIIMBOT_PLUGIN_VERSION,

    author="piramja",

    author_email="info@piramja.de",

    description="Niimbot label printer (b1, b18, b21, d11, d110) plugin for InvenTree",

    long_description=long_description,

    long_description_content_type='text/markdown',

    keywords="inventree inventreeplugins label printer printing inventory niimbot",

    url="https://github.com/piramja/inventree-niimbot-plugin",

    license="MIT",

    packages=setuptools.find_packages(),

    install_requires=[
        # bleak removed: only needed for Bluetooth, we use USB serial.
        # Pinned 0.21.1 doesn't support Python 3.14 (InvenTree 1.3.x).
        'devtools>=0.12',
        'loguru>=0.7',
        # pillow removed: InvenTree already ships it.
        # setuptools/markdown-it-py removed: InvenTree already ships them.
        'pyserial>=3.5',
    ],

    setup_requires=[
        "wheel",
        "twine",
    ],

    python_requires=">=3.10",

    entry_points={
        "inventree_plugins": [
            "NiimbotLabeLPlugin = inventree_niimbot.niimbot_plugin:NiimbotLabelPlugin"
        ]
    },

    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Framework :: InvenTree",
    ],
)
