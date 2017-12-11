#!/usr/bin/env python

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

setup(	name='MIPPY',
		version='1.0.4',
		description='Modular Image Processing in Python',
		author='Robert Flintham',
		author_email='robert.flintham@uhb.nhs.uk',
		install_requires=['numpy','scipy','pydicom','pillow','nibabel','matplotlib'],
		license='BSD-3-Clause',
		classifiers=[
			'Development Status :: 1 - Alpha',
			'Intended Audience :: Developers',
			'Programming Language :: Python :: 2.7',
			],
		packages=['mippy','mippy.mdicom','mippy.mviewer'],
		package_data={'':['resources/*','mviewer/config']}
	)
