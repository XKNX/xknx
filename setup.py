"""Setup for XKNX python package."""
from os import path

from setuptools import find_packages, setup

THIS_DIRECTORY = path.abspath(path.dirname(__file__))
with open(path.join(THIS_DIRECTORY, "README.md"), encoding="utf-8") as f:
    LONG_DESCRIPTION = f.read()

VERSION = {}
# pylint: disable=exec-used
with open(path.join(THIS_DIRECTORY, "xknx/__version__.py"), encoding="utf-8") as fp:
    exec(fp.read(), VERSION)

REQUIRES = ["netifaces>=0.10.9"]

setup(
    name="xknx",
    description="An Asynchronous Library for the KNX protocol. Documentation: https://xknx.io/",
    version=VERSION["__version__"],
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    download_url=f"https://github.com/XKNX/xknx/archive/{VERSION['__version__']}.zip",
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
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    packages=find_packages(include=["xknx", "xknx.*"]),
    package_data={"xknx": ["py.typed"]},
    include_package_data=True,
    install_requires=REQUIRES,
    keywords="knx ip knxip eib home automation",
    zip_safe=False,
)
