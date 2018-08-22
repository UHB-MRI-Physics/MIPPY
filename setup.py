from setuptools import setup, find_packages
from codecs import open
from os import path
import sys

here = path.abspath(path.dirname(__file__))



    
##################################

def get_version():
    import mippy
    return mippy.__version__

def check_version():
    version = get_version()
    print(version)
    import datetime
    import os
    # Get timestamp for __init__.pyc
    version_time = datetime.datetime.fromtimestamp(os.path.getmtime(r'mippy\__pycache__\__init__.cpython-36.pyc'))
    print(version_time)
    other_times = []
    for root, dirs, files in os.walk(os.get_cwd()):
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
            print(tstamp)
            break
    if code_changed:
        print("CANNOT COMPILE - VERSION NUMBER OUTDATED")
        import sys
        sys.exit()
    return


# Test version numbering before running setup
# Only if not run by pytest
try:
    if sys.argv[2]=='bdist_wheel':
        do_check_version = True
    else:
        do_check_version = False
except:
    do_check_version = False
if do_check_version:
    # This should only work if running bdist_wheel locally
    check_version()

setup(        name='MIPPY',
                version=get_version(),
                description='Modular Image Processing in Python',
                author='Robert Flintham',
                author_email='robert.flintham@uhb.nhs.uk',
                install_requires=['numpy>=1.15.0',
                                  'scipy>=1.1.0',
                                  'pydicom>=1.0.2',
                                  'pillow>=5.1.0',
                                  'nibabel>=2.2.1',
                                  'matplotlib>=2.2.2',
                                  'easygui'],
                license='BSD-3-Clause',
                classifiers=[
                        'Programming Language :: Python :: 3.6',
                        ],
                packages=['mippy','mippy.mdicom','mippy.mviewer'],
                package_data={'':['resources/*','mviewer/config']}
        )
