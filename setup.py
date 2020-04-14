"""Setup for XKNX python package."""
from os import environ, path
from setuptools import find_packages, setup

VERSION = environ.get('GITHUB_REF', 'dev')

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

REQUIRES = [
    'pyyaml>=5.1',
    'netifaces>=0.10.9'
]

setup(
    name='xknx',
    description='An Asynchronous Library for the KNX protocol. Documentation: https://xknx.io/',
    version=VERSION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    download_url='https://github.com/XKNX/xknx/archive/{}.zip'.format(VERSION),
    url='https://xknx.io/',
    author='Julius Mittenzwei',
    author_email='julius@mittenzwei.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'Topic :: System :: Hardware :: Hardware Drivers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8'
    ],
    packages=find_packages(),
    install_requires=REQUIRES,
    keywords='knx ip knxip eib home automation',
    zip_safe=False)
