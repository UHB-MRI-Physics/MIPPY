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
##                print tstamp, version_time, tstamp>version_time
                if tstamp>version_time:
                        code_changed = True
                        print(tstamp)
                        break
        if code_changed:
                print("CANNOT COMPILE - VERSION NUMBER OUTDATED")
                import sys
                sys.exit()
        return
    
# Determine version number from BUILD tags on gitlab
try:
	if os.environ.get('CI_COMMIT_TAG'):
			if os.environ['CI_COMMIT_TAG'].startswith('v'):
				version = os.environ['CI_COMMIT_TAG'][1:]
			else:
				version = os.environ['CI_COMMIT_TAG']
	else:
		version = '0.'+os.environ['CI_JOB_ID'] # Use job ID if no commmit tag provided
except KeyError:
	import datetime
	version='0.'+str(datetime.datetime.now())[0:23].replace(' ','-').replace(':','')

with open('requirements.txt','r') as f:
	requirements = f.readlines()

setup(       name='mippy',
                version=version,
                description='Modular Image Processing in Python',
                author='Robert Flintham',
                author_email='rbf906@gmail.com',
                license='BSD-3-Clause',
                classifiers=[
                        'Programming Language :: Python :: 3',
                        ],
                install_requires=requirements,
                packages=['mippy','mippy.mdicom','mippy.mviewer'],
                scripts=['scripts/mippy.bat','scripts/_mippy.py','scripts/install_mippy.bat','scripts/install_mippy.py'],
                url='https://tree.taiga.io/project/robflintham-mippy/',
                package_data={'':['resources/*','mviewer/config']}
        )
