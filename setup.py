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
      package_dir={'st2g': 'src'},
      install_requires=[
          "argparse>=1.4.0",
          "sqlparse>=0.3.0",
          "spacy>=2.1.0",  # new version uncompatible with neuralcoref
          "graphviz>=0.13",
          # "neuralcoref>=4.0",
      ],
      tests_require=['pytest'],
      entry_points={
          'console_scripts': [
              'st2g = st2g.main:main',
          ],
      }
      )
