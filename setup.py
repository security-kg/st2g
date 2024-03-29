#!/usr/bin/env python

from setuptools import setup, find_packages

# print(find_packages('src', exclude=["*.tests", "*.tests.*", "tests.*", "tests"]))

setup(name='st2g',
      version='0.0',
      description='Covert security articles to graph representations',
      author='littleRound',
      author_email='lxy9843@gmail.com',
      url='https://github.com/security-kg/st2g/',
      packages=find_packages('src', exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
      package_dir={'': 'src'},
      include_package_data=True,
      install_requires=[
          "argparse>=1.4.0",
          "sqlparse>=0.3.0",
          "numpy==1.15.0",
          "spacy==2.2.1",
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
