from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

### THESE FUNCTIONS USED TO DETECT IF THIS IS
### BEING RUN FROM WITHIN PYTEST

def pytest_configure(config):
    import sys
    sys._called_from_test = True

def pytest_unconfigure(config):
    import sys  # This was missing from the manual
    del sys._called_from_test


    
##################################

def get_version():
    import mippy
    return mippy.__version__

def test_version():
    version = get_version()
    print(version)
    import datetime
    import os
    # Get timestamp for __init__.pyc
    version_time = datetime.datetime.fromtimestamp(os.path.getmtime(r'mippy\__pycache__\__init__.cpython-36.pyc'))
    print(version_time)
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
            print(tstamp)
            break
    if code_changed:
        print("CANNOT COMPILE - VERSION NUMBER OUTDATED")
        import sys
        sys.exit()
    return


# Test version numbering before running setup
# Only if not run by pytest
if not hasattr(sys, '_called_from_test'):
    test_version()

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
