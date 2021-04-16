# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='argustal',
    version='0.1.0',
    description='Timeseries Abstraction Layer for ArgusIoT',
    long_description=readme,
    author='Parag Panse',
    author_email='paragpm@argusanalytics.io',
    url='https://github.com/argusiot/data_platform',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)

