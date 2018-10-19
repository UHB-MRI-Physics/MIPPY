mippy.viewing
##################################

.. module:: mippy.viewing
.. currentmodule:: mippy.viewing

This module contains the key image viewing/displaying classes and
functions in MIPPY.  If you want to work with images on a canvas,
this is probably the right place to look.


ImageFlipper (Class)
========================================

.. autoclass:: ImageFlipper
    :members:


MIPPYCanvas (Class)
=========================================

.. autoclass:: MIPPYCanvas
    :members:
    :exclude-members: rescale_rois, reconfigure, scroll_images, update_scrollbar, update_roi_masks, update_all_roi_masks, left_click, left_drag, left_release, left_double, right_click, right_drag, right_release, right_double
    

ROI (Class)
==========================================

.. autoclass:: ROI
    :members:


Functions
=========================================

.. autofunction:: bits_to_ndarray

.. autofunction:: generate_px_float

.. autofunction:: get_ellipse_coords

.. autofunction:: get_global_min_and_max

.. autofunction:: get_overlay

.. autofunction:: px_bytes_to_array

.. autofunction:: quick_display

