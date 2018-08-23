from setuptools import setup, find_packages
from codecs import open
from os import path
import sys
import os

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
#~ try:
    #~ if 'bdist_wheel' in sys.argv:
        #~ do_check_version = True
    #~ else:
        #~ do_check_version = False
#~ except:
    #~ do_check_version = False
#~ if do_check_version:
    #~ # This should only work if running bdist_wheel locally
    #~ check_version()
    
# Determine version number from BUILD tags on gitlab??
if os.environ.get('CI_COMMIT_TAG'):
        version = os.environ['CI_COMMIT_TAG']
else:
        version = os.environ['CI_JOB_ID'] # Use job ID if no commmit tag provided

setup(        name='MIPPY',
                version=version,
                description='Modular Image Processing in Python',
                author='Robert Flintham',
                author_email='rbf906@gmail.com',
                license='BSD-3-Clause',
                classifiers=[
                        'Programming Language :: Python :: 3',
                        ],
                packages=['mippy','mippy.mdicom','mippy.mviewer'],
                url='https://tree.taiga.io/project/robflintham-mippy/',
                package_data={'':['resources/*','mviewer/config']}
        )
