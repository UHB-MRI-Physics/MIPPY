Quick Reference
###################


ROIs (Regions of Interest)
==============================

.. _useful-roi-tags:

Useful tags
---------------------------------------

Tags can be used to control the appearance of ROIs.  In order to create
dashed or stippled/shaded ROIs, the following tags can be specified when
you generate your ROI:

+----------------------------------------------------------------------------------------+
| Useful tags:                                                                           |
+-----------------+----------------------------------------------------------------------+
| ``'dash'``      | Dashed border to ROI - must also specify the type of dash            |
+-----------------+----------------------------------------------------------------------+
| ``'dash42'``    | Dashes of length 4 with a gap of 2 - to be used with ``'dash'``      |
+-----------------+----------------------------------------------------------------------+
| ``'dash44'``    | Dashes of length 4 with a gap of 4 - to be used with ``'dash'``      |
+-----------------+----------------------------------------------------------------------+
| ``'dash22'``    | Dashes of length 2 with a gap of 2 - to be used with ``'dash'``      |
+-----------------+----------------------------------------------------------------------+
| ``'stipple'``   | Stipple-fill the ROI - must also specify the type of stipple         |
+-----------------+----------------------------------------------------------------------+
| ``'gray25'``    | Stipple with 25% coverage - to be used with ``'stipple'``            |
+-----------------+----------------------------------------------------------------------+
| ``'gray50'``    | Stipple with 50% coverage - to be used with ``'stipple'``            |
+-----------------+----------------------------------------------------------------------+
| ``'gray75'``    | Stipple with 75% coverage - to be used with ``'stipple'``            |
+-----------------+----------------------------------------------------------------------+