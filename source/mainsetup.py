# -*- coding: utf-8 -*-
"""
Created on Fri Dec  9 12:17:11 2016

Setup script for dicom_functions

@author: rob
"""

from distutils.core import setup
from Cython.Build import cythonize

setup(
	name = 'MIPPY Main',
	ext_modules = cythonize('main.pyx')
	)