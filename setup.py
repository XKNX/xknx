from setuptools import setup, find_packages

setup(name='xknx',
      version='0.1',
      description='A Wrapper around KNX/UDP protocol written in python.',
      url='https://github.com/julius2342/xknx',
      author='Julius Mittenzwei',
      author_email='julius@mittenzwei.com',
      license='MIT',
      classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'Topic :: System :: Hardware :: Hardware Drivers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5'
        ],
      packages=find_packages(),
      keywords = 'knx ip automation',
      zip_safe=False)
