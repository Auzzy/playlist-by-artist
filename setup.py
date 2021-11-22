from setuptools import find_packages, setup

from playlistmanager import __version__

setup(
    name='playlistmanager',
    version=__version__,
    author="Austin Noto-Moniz",
    author_email="mathfreak65@gmail.com",
    packages=find_packages(),
    python_requires='>=3.6'
)
