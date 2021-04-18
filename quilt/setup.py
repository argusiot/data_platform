# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='argusquilt',
    version='0.1.0',
    description='Argus Quilt: Stitch timeseries to develop appliqe',
    long_description=readme,
    install_requires=['jsonschema'],
    author='Parag Panse, Vishwas Lokesh',
    author_email='paragpm@argusanalytics.io',
    url='https://github.com/argusiot/data_platform',
    license=license,
    packages=find_packages(exclude=('integration_tests', 'poc', 'tests'))
)
