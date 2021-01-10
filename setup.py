"""Setup for XKNX python package."""
from os import path

from setuptools import find_packages, setup

THIS_DIRECTORY = path.abspath(path.dirname(__file__))
with open(path.join(THIS_DIRECTORY, "README.md"), encoding="utf-8") as f:
    LONG_DESCRIPTION = f.read()

VERSION = {}
# pylint: disable=exec-used
with open(path.join(THIS_DIRECTORY, "xknx/__version__.py")) as fp:
    exec(fp.read(), VERSION)

REQUIRES = ["pyyaml>=5.1", "netifaces>=0.10.9", "voluptuous>=0.12.0"]

setup(
    name="xknx",
    description="An Asynchronous Library for the KNX protocol. Documentation: https://xknx.io/",
    version=VERSION["__version__"],
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    download_url="https://github.com/XKNX/xknx/archive/{}.zip".format(
        VERSION["__version__"]
    ),
    url="https://xknx.io/",
    author="Julius Mittenzwei",
    author_email="julius@mittenzwei.com",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "Topic :: System :: Hardware :: Hardware Drivers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    packages=find_packages(include=["xknx", "xknx.*"]),
    install_requires=REQUIRES,
    keywords="knx ip knxip eib home automation",
    zip_safe=False,
)
