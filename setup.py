from setuptools import find_packages, setup

from playlistmanager import __version__

setup(
    name='playlistmanager',
    version=__version__,
    author="Austin Noto-Moniz",
    author_email="mathfreak65@gmail.com",
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=[
        "requests >= 2.26.0",
        "Unidecode >= 1.3.2",
        "ytmusicapi >= 0.19.4, < 1.0",
        "bs4"
    ]
)
