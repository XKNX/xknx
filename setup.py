from setuptools import setup, find_packages

setup(
        name='xknx',
        description='A Wrapper around KNX protocol.',

        version='0.3.1',
        download_url='https://github.com/XKNX/xknx/archive/0.3.1.zip',
        url='http://xknx.io/',

        author='Julius Mittenzwei',
        author_email='julius@mittenzwei.com',
        license='MIT',
        classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: End Users/Desktop',
          'Intended Audience :: Developers',
          'Topic :: System :: Hardware :: Hardware Drivers',
          'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5'
        ],
        packages=find_packages(),
        install_requires=['PyYAML'],
        keywords = 'knx ip knxip eib home automation',
        zip_safe=False)
