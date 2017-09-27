#!/usr/bin/env python

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

setup(	name='MIPPY',
		version='1.0.1',
		description='Modular Image Processing in Python',
		author='Robert Flintham',
		author_email='robert.flintham@uhb.nhs.uk',
		install_requires=['numpy','scipy','pydicom','pillow'],
		license='MIT',
		classifiers=[
			'Development Status :: 3 - Alpha',
			'Intended Audience :: Developers',
			'Programming Language :: Python :: 2.7',
			],
		packages=['mippy','mippy.mdicom'],
		package_data={'':['resources/*']}
	)