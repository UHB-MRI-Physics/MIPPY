# MIPPY: Modular Image Processing in Python

## Introduction

MIPPY is an application written in Python to organise, read, view and analyse DICOM format images. It was written primarily for analysis of MRI quality assurance data, but can be (and has been) extended to other analysis techniques such as T1 mapping and ASL data analysis. It is free to download and install, and was created by the MRI physics team at University Hospitals Birmingham, UK.

## Installation Instructions

### Windows

Install python 3.7, and use pip to install the mippy package:

`pip install mippy`

Once the mippy package is installed, run the secondary installation script that comes bundled with the package. If your python environment variables are set correctly, you should be able to just run (from a command prompt window):

`install_mippy`

If this doesn't work, navigate to your python installation directory and the 'scripts' folder within it, and manually run `install_mippy.bat`.

This script should create you a user-specific installation directory on your C drive and a 'modules' directory within this. This modules folder is the default installation location for modules, and is the place MIPPY will scan for modules by default when you launch the program.

It should also add MIPPY to your Windows start menu. This is usually the best way to launch the program, although it can also be launched with the 'start_mippy' script located in your new C/MIPPY directory.

**IMPORTANT: There is a known issue behind proxies with the latest versions of pip. If you are getting SSL errors when you are running pip, please downgrade pip manually to version 20.2.1 and this will fix this error.** There are probably other fixes where you properly configure your https proxies, but for the time being, this seems to do the job.

### Mac and others

Installation of the package is largely the same, except you will need to run `pip3 install mippy` instead of `pip install mippy`. You may also need to manually install a version of python through your package manager which includes tkinter, as the default version of python3 preloaded onto your system may not contain this.

However, beyond this point you're kind of on your own. The best way to do things is probably to create yourself a shell script or another form of link to launch the _mippy.py script directly from within your python install folder. This hasn't really been thoroughly tested though, and it's very much aimed at Windows systems.


## Usage

After starting MIPPY, use the FILE menu to open the directory containing your images. MIPPY will read the directory and organise images by patient, study and series. From here you can select which images you are interested in, and load them into any modules you have available.

## Contributing

Contributors and developers are welcomed with open arms! However, given the infant stage of this project, we ask that would-be developers get in touch so we can add you to the project and keep a handle on who's doing what.  The developers can be contacted via the Google group (see below).

For bug/issue reporting, please head here:
https://gitlab.com/rbf906/mippy/issues

The code is available here:
https://gitlab.com/rbf906/mippy/tree/master

## Help

For all help, issues, bug reports and feature requests, use the Google group:
https://groups.google.com/forum/#!forum/mippyusers

## Authors

- Robert Flintham
- RW

## Contact

Best method of contact is via the Google Group (see above).

## License

This project is licensed under the BSD license.
