# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['usgs_mbe']

package_data = \
{'': ['*']}

install_requires = \
['lxml>=4.6.3,<5.0.0',
 'pandas>=1.2.4,<2.0.0',
 'requests>=2.25.1,<3.0.0',
 'xmltodict>=0.12.0,<0.13.0']

entry_points = \
{'console_scripts': ['usgs_mbe = usgs_mbe:main.cli']}

setup_kwargs = {
    'name': 'usgs-mbe',
    'version': '0.1.1',
    'description': 'USGS MovingBedExtraction - Parser to generate summary data from ADCP files for the USGS.',
    'long_description': '# ADCP-Moving-Bed-Extraction\nPulls extraction files from ADCP files for the USGS. Can be run on a given folder with subdirectories. For all the subdirectories - the script will scan through all files looking for two conditions:\n1) File extension is xml\n2) `QRev` (case sensitive) is present in the file name. \n\nAn error log will be generated to the folder. There may be some bad field data / assumptions taken, and the script will do its best to inform you of those decisions.\n\n# Installation\n`pip install usgs_mbe`\n\n# Usage\n`usgs_mbe --test-folder=/path/to/folder` \n\nor - more simply - \n\n`usgs_mbe` \n\n# Output \n\nA csv file in each subfolder with the following columns:\n```\nMovingBedSpeed\nMovingBedSpeedUnit\nTestTimestamp\nMovingBedTestResults\nStationName\nsiteid\nMovingBedTestQuality\nDuplicates -- If multiple values were found - this indicates that the first was taken.\ngage_height_va -- USGS value for the closest height to the TestTimestamp.\n```',
    'author': 'Nick Benthem',
    'author_email': 'nick@benthem.io',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/NickBenthem/ADCP-Moving-Bed-Extraction',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
