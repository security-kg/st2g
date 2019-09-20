#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='st2g',
      version='0.0',
      description='Covert security articles to graph representations',
      author='littleRound',
      author_email='lxy9843@gmail.com',
      url='https://github.com/camelop/securitytext2graph',
      packages=find_packages(exclude=["*.tests", "*.tests.*",
                                      "tests.*", "tests"]),
      package_dir={'': 'src'},
      install_requires=[
          "argparse>=1.4.0",
          "spacy",
      ],
      tests_require=['pytest'],
      entry_points={
          'console_scripts': [
              'st2g = st2g.main:main',
          ],
      }
      )
