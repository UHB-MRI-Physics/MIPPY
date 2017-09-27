#!/usr/bin/env python

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

setup(	name='MIPPY',
		version='0.20.1',
		description='Medical Image Processing in Python',
		author='Robert Flintham',
		author_email='robert.flintham@uhb.nhs.uk',
		install_requires=['numpy','scipy','pydicom','pillow'],
		license='MIT',
		classifiers=[
			'Development Status :: 3 - Alpha',
			'Intended Audience :: Developers',
			'Programming Language :: Python :: 2.7',
			],
		packages=['mippy','mippy.mdicom','mippy.mviewer'],
		package_data={'':['resources/*','mviewer/config']}
	)