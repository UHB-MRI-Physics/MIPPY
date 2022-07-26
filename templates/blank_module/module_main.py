"""
Blank module template for MIPPY

This is a simple module template containing 1 canvas, 1 button and an
output text box
"""
version = "1.0.0" # Needs to be string format - not used in the current version of MIPPY anyway

# Import statements - you might not need all of these, but these can be a good starting point
from tkinter import *
from tkinter.ttk import *
import tkinter.messagebox
from mippy.viewing import *
import mippy.improcess as imp
from mippy.math import intround
from mippy.html import MarkdownWindow,markdown_to_browser
import os
from PIL import Image, ImageTk
import gc
import datetime
import difflib

from importlib import reload
try:
    reload(mri_dicom_miner)
except NameError:
    from rrpps_mri_misc import mri_dicom_miner
from rrpps_mri_misc.mri_dicom_miner import collect_acq_info,json_print

try:
    reload(db_test)
except NameError:
    from rrpps_mri_misc import db_test

try:
    reload(widgets)
except NameError:
    from rrpps_mri_misc import widgets

DATABASE_ACTIVE = db_test.DATABASE_ACTIVE()


def check_version():
    # This isn't actually used any more in the current version of MIPPY
    return version


def preload_dicom():
    """
    This method is essential for the module to run. MIPPY needs to know whether
    the module wants preloaded DICOM datasets or just paths to the files.  Most
    modules will probably want preloaded DICOM datasets so that you don't have
    to worry about different manufacturers, enhanced vs non-enhanced etc.
    However, I imagine some people will prefer to work with the raw data files
    and open the datasets themselves for e.g. better memory use
    """
    # If you want DICOM datasets pre-loaded, return True.
    # If you want paths to the files only, return False.
    # Note the capital letters on True and False.  These are important.
    return True


def flatten_series():
    """
    By default, MIPPY will pass the image datasets as a 2D list, divided by series.
    If you want only a single, flat list from all your series, return True.
    """
    return True


def execute(master_window, instance_info, images):
    """
    This is the function that will run when you run the program. If you create a GUI
    window, use "master_window" as its master.  "dicomdir" is the dicom directory
    that has been loaded, and may or may not be where you want to save any
    result images.  "images" is a list containing your image datasets.  If you have
    set the "preload_dicom" message above to "return True", these will be dicom
    datasets.  If you set "return False", these will just be paths to the image files.
    """

    """
    This section creates you blank GUI and sets your window title and icon.
    """

    win = Toplevel(master_window)   # Create your main window
    win.instance_info = instance_info   # Store the instance info for use later

    # Give the window a title
    win.title("{} {}: {}".format(win.instance_info['module_name'],win.instance_info['module_version'],win.instance_info['module_instance']))
    # Store a referennce to the file path
    win.fpath = __file__
    # Store a reference to the temp directory
    win.tempdir = os.path.join(win.instance_info['temp_directory'],win.instance_info['module_instance'])


    gc.collect() # Just runs a manual garbage collect, can be useful in debugging

    # These two commands set default module behaviour - first one sets the file menu,
    # second one unpacks any documentation/help folders if archived
    print("Setting menu")
    widgets.set_menu(win)
    print("Extracting docs")
    widgets.extract_docs(win)

    # Useful option if you want to adjust the default window size based on the screen
    # resolution
    win.screenwidth = win.winfo_screenwidth()
    win.screenheight = win.winfo_screenheight()

    if win.screenheight < 800 or win.screenwidth < 1200:
        imwidth = 400
        imheight = 400
    else:
        imwidth = 700
        imheight = 700


    # Create a canvas
    win.im1 = MIPPYCanvas(win, width=imwidth, height=imheight, drawing_enabled=True, antialias=False, use_masks=False)
    # IMPORTANT
    # use_masks=False generates errors if you resize the image after resizing the canvas.

    # Set a scrollbar
    win.im1.img_scrollbar = Scrollbar(win, orient='horizontal')
    win.im1.configure_scrollbar()

    # Create a toolbar for your buttons
    win.toolbar = Frame(win)

    # Create a button
    win.button_1 = Button(win.toolbar, text='Button 1', command=lambda: button_1_callback(win))

    # An outputbox can be useful
    win.outputbox = Text(win, state='disabled', height=10, width=60)

    # Position your buttons on the toolbar
    win.button_1.grid(row=4, column=0, sticky='ew')

    # Position your larger objects
    win.im1.grid(row=1, column=0, rowspan=2, sticky='nsew')
    win.im1.img_scrollbar.grid(row=3, column=0, sticky='ew')
    win.toolbar.grid(row=1, column=1, rowspan=2, sticky='nsew')
    win.outputbox.grid(row=4, column=0, columnspan=2, sticky='nsew')

    # Control which rows/coumns can resize
    win.rowconfigure(0, weight=0)
    win.rowconfigure(1, weight=1)
    win.rowconfigure(2, weight=1)
    win.rowconfigure(3, weight=0)
    win.rowconfigure(4, weight=0)
    win.columnconfigure(0, weight=1)
    win.columnconfigure(1, weight=0)

    win.toolbar.columnconfigure(0, weight=1)

    # Load your images on the canvas
    win.im1.load_images(images)
    win.im1.show_image(1)
    win.images = images
    win.iminfo = [[]]

    for im in win.images:
        win.iminfo[0].append(collect_acq_info(im))

    return


def close_window(window):
    """Closes the window passed as an argument"""
    active_frame.destroy()
    return


def output(win, txt):
    win.outputbox.config(state=NORMAL)
    win.outputbox.insert(END, txt + '\n')
    win.outputbox.config(state=DISABLED)
    win.outputbox.see(END)
    win.update()
    return


def clear_output(win):
    win.outputbox.config(state=NORMAL)
    win.outputbox.delete('1.0', END)
    win.outputbox.config(state=DISABLED)
    win.update()


def button_1_callback(win):
    # This is the function the button runs
    return
