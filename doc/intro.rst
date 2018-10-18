Introduction
#############################

What is MIPPY?
===============================

MIPPY is a python library for interacting graphically with DICOM image files.  It includes a GUI application for inspecting folders of DICOM images, selecting images/series/studies of interest and launching image analysis modules.  Any number of custom-built modules can be added to MIPPY.

The MIPPY library includes built-in classes and functions to handle image display and windowing, region-of-interest (ROI) drawing/analysis and feature/overlay drawing (e.g. MR saturation regions).  It relies heavily on the python modules **numpy** and **tkinter**.

Purpose and Scope
===================================

MIPPY is...
---------------------

MIPPY is a framework within which you can develop custom image analyis techniques for direct analysis of DICOM image data, *without* the need for image sorting or conversion to alternative formats (e.g. NIFTI or ANALYZE).

MIPPY does most of the heavy lifting for you to achieve:

* reading directories of DICOM files and sorting by patient/series/study
* loading and displaying single or multiple DICOM images
* ROI drawing and analsyis
* creation of DICOM images (e.g. results/maps)
* passing delected DICOM data to custom Python analysis scripts

MIPPY is intended primarily to be used as an application via its GUI.  However, it doesn't have to be.  You can import modules, classes and functions from within MIPPY for use in other code.

MIPPY is not...
----------------------------

MIPPY is wonderful, but is it **not** intended to...

* ...be a PACS system or patient/image database.
* ...parse DICOM files directly (it uses PyDICOM; anything PyDICOM can't read, MIPPY can't either).
* ...be a direct replacement for the DICOM toolkit in Matlab, or any similar packagaes.  Some functionality of these will inevitably be replicated in MIPPY, but this is not the intention.
* ...be a development environment.
* ...perform any analysis for *real clinical purposes*.  The authors make no guarantees about the code, and as such, do not recommend its use for anything which impacts clinical decision making.  MIPPY is a research, development and testing tool only.  Please see the LICENSE for detailed information on what you are permitted to do with MIPPY and its source code.


Software Design
===================================

Source code structure
----------------------------

| mippy
| +-- doc
| +-- resources
| +-- LICENSE
| +-- README.md
| +-- requirements.txt
| +-- ``setup.py``
| +-- mippy
|     +-- ``application.py``        *[Contains the main GUI class for MIPPY (MIPPYMain)]*
|     +-- ``fileio.py``             *[File reading and writing]*
|     +-- ``improcess.py``          *[General functions for imaging processing/analysis]*
|     +-- ``launcher.py``           *[Launcher for the MIPPY GUI]*
|     +-- ``math.py``               *[Useful math functions]*
|     +-- ``misc.py``               *[Miscellaneous functions]*
|     +-- ``splash.py``             *[Handles splash screen displaying at program startup]*
|     +-- ``threading.py``          *[Multithreading / parallel processing]*
|     +-- ``viewing.py``            *[All main classes and functions to handle image viewing and interaction]*
|     +-- mdicom
|         +-- ``anon.py``               *[Functions related to handling anonymous data or removal of patient information]*
|         +-- ``io.py``                 *[Input/output of DICOM files]*
|         +-- ``mrenhanced.py``         *[Tools for dealing with MR spectroscopy data]*
|         +-- ``mrspectroscopy.py``     *[Tools for dealing with MR spectroscopy data]*
|         +-- ``pixel.py``              *[Handling pixel data from DICOM instances]*
|         +-- ``reading.py``            *[Reading/sorting DICOM files]*
|         +-- ``siemens.py``            *[Functions specific to SIEMENS equipment and private CSA headers]*
|     +-- mviewer
|         +-- ``module_main.py``        *[Source code for the "Image Viewer" module in MIPPY]*
|         +-- ``module_config.py``      *[Produces the config file required by MIPPY to recognise a module]*
|         +-- config

