README v0.0 / 28 JUNE 2015
(TEST EDIT)

# MIPPY: Modular Image Processing in Python

## Introduction

MIPPY is a framework written in Python (2.7) to organise, read, view and analyse DICOM format images. It was written primarily for analysis of MRI quality assurance data, but can be (and has been) extended to other analysis techniques such as T1 mapping and ASL data analysis. It is free to download and install, and was created by the MRI physics team at University Hospital Birmingham, UK.

## Usage

After starting MIPPY, use the FILE menu to open the directory containing your images. MIPPY will read the directory and organise images by patient, study and series. From here you can select which images you are interested in, and load modules such as "Image Viewer" and "Image Uniformity Analysis".

## Contributing

Contributors and developers are welcomed with open arms! However, given the infant stage of this project, we ask that would-be developers get in touch so we can add you to the project and keep a handle on who's doing what.  The developers can be contacted via the Google group (see below).

For bug/issue reporting, please head here:
https://gitlab.com/rbf906/mippy/issues

The code is available here:
https://gitlab.com/rbf906/mippy/tree/master

## Help

For all help, issues, bug reports and feature requests, use the Google group:
https://groups.google.com/forum/#!forum/mippyusers

## Installation

### Requirements

MIPPY relies on a number of external python packages, all available via PyPI:
- PyDICOM
- NumPy
- SciPy
- Pillow (PIL fork)


### Configuration

There should be no further configuration required after installation.

## Authors

- Robert Flintham
- RW

## Contact

Best method of contact is via the Google Group (see above).

## License

This project is licensed under the BSD license.