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
        'bleak==0.21.1',
        'devtools==0.12.2',
        'setuptools==69.5.1',
        'markdown-it-py==3.0.0',
        'loguru==0.7.2',
        # pillow removed: InvenTree already ships it.
        # The pinned version caused an incomplete install into /root/.local/
        # that shadowed the working system Pillow, breaking all label printing.
        # See: https://github.com/piramja/inventree-niimbot-plugin/issues/4
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
