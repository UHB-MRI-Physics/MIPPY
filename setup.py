#!/usr/bin/env python

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

def get_version():
    import mippy
    return mippy.__version__

def test_version():
    version = get_version()
    import datetime
    import os
    # Get timestamp for __init__.pyc
    version_time = datetime.datetime.fromtimestamp(os.path.getmtime(r'mippy\__init__.pyc'))
    other_times = []
    for root, dirs, files in os.walk('mippy'):
        for f in files:
            fpath = os.path.join(root,f)
            lastdir = os.path.split(os.path.split(fpath)[0])[1]
            if os.path.splitext(fpath)[1]=='.py' or lastdir=='resources':
                other_times.append(datetime.datetime.fromtimestamp(os.path.getmtime(fpath)))
    code_changed = False
    for tstamp in other_times:
##        print tstamp, version_time, tstamp>version_time
        if tstamp>version_time:
            code_changed = True
            break
    if code_changed:
        print("CANNOT COMPILE - VERSION NUMBER OUTDATED")
        import sys
        sys.exit()
    return


# Test version numbering before running setup
test_version()

setup(        name='MIPPY',
                version=get_version(),
                description='Modular Image Processing in Python',
                author='Robert Flintham',
                author_email='robert.flintham@uhb.nhs.uk',
                install_requires=['numpy','scipy','dicom','pillow','nibabel','matplotlib'],
                license='BSD-3-Clause',
                classifiers=[
                        'Programming Language :: Python :: 2.7',
                        ],
                packages=['mippy','mippy.mdicom','mippy.mviewer'],
                package_data={'':['resources/*','mviewer/config']}
        )
