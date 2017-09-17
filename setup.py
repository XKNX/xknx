"""Setup for XKNX python package."""
from setuptools import setup, find_packages

VERSION = '0.7.14'

REQUIRES = ['PyYAML', 'netifaces']

setup(
    name='xknx',
    description='An Asynchronous Library for the KNX protocol. Documentation: http://xknx.io/',

    version=VERSION,
    download_url='https://github.com/XKNX/xknx/archive/'+VERSION+'.zip',
    url='http://xknx.io/',

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
        'Programming Language :: Python :: 3.6'
    ],
    packages=find_packages(),
    install_requires=REQUIRES,
    keywords='knx ip knxip eib home automation',
    zip_safe=False)
