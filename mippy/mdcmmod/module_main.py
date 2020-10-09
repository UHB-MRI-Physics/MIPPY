from tkinter import *
# from tkinter.ttk import *
import tkinter.messagebox
from mippy.viewing import *
import os
from PIL import Image,ImageTk
import platform
from pkg_resources import resource_filename

def preload_dicom():
    """
    This method is essential for the module to run. MIPPY needs to know whether
    the module wants preloaded DICOM datasets or just paths to the files.  Most
    modules will probably want preloaded DICOM datasets so that you don't have
    to worry about different manufacturers, enhanced vs non-enhanced etc.
    However, I imagine some people will prefer to work with the raw data files
    and open the datasets themselves?
    """
    # If you want DICOM datasets pre-loaded, return True.
    # If you want paths to the files only, return False.
    # Note the capital letters on True and False.  These are important.
    return False

def flatten_series():
    """
    By default, MIPPY will pass the image datasets as a 2D list, divided by series.
    If you want only a single, flat list from all your series, return True.
    """
    return False


def execute(master_window,instance_info,images):
    print("Module loaded...")
    print("Received "+str(len(images))+" image datasets.")
    print(os.getcwd())
    #~ icondir = os.path.join(os.getcwd(),'source','images')


    # This is to fix backwards compatibility for anywhere the old dicomdir object
    # was used
    dicomdir = instance_info['image_directory']

    win = Toplevel(master_window)
    win.instance_info = instance_info
    win.title("{} {}: {}".format(win.instance_info['module_name'],win.instance_info['mippy_version'],win.instance_info['module_instance']))
    win.fpath = __file__
    win.tempdir = os.path.join(win.instance_info['temp_directory'],win.instance_info['module_instance'])
    win.images = images

    build_window(win)

    get_details(win)





def close_window(win):
        win.destroy()
        return

def apply_changes(win):
    pass

def build_window(win):
    win._patient_details = Label(win,text="Patient Details").grid(row=0,column=0,columnspan=2)
    win._family_name = Label(win,text="Family Name").grid(row=1,column=0)
    # win.family_name = StringVar()
    win.family_name_e = Entry(win,width=40,textvariable=win.family_name).grid(row=1,column=1)
    win._given_name = Label(win,text="Given Name").grid(row=2,column=0)
    # win.given_name = StringVar()
    win.given_name_e = Entry(win,width=40,textvariable=win.given_name).grid(row=2,column=1)
    win._middle_name = Label(win,text="Middle Name").grid(row=3,column=0)
    # win.middle_name = StringVar()
    win.middle_name_e = Entry(win,width=40,textvariable=win.middle_name).grid(row=3,column=1)
    win._patient_title = Label(win,text="Title").grid(row=4,column=0)
    # win.patient_title = StringVar()
    win.patient_title_e = Entry(win,width=40,textvariable=win.patient_title).grid(row=4,column=1)
    win._suffix = Label(win,text="Suffix").grid(row=5,column=0)
    # win.suffix = StringVar()
    win.suffix_e = Entry(win,width=40,textvariable=win.suffix).grid(row=5,column=1)
    win._phonetic = Label(win,text="Phonetic Name").grid(row=6,column=0)
    # win.phonetic = StringVar()
    win.phonetic_e = Entry(win,width=40,textvariable=win.phonetic).grid(row=6,column=1)
    win._dob = Label(win,text="Date of Birth (DD/MM/YYYY)").grid(row=7,column=0)
    # win.dob = StringVar()
    win.dob_e = Entry(win,width=40,textvariable=win.dob).grid(row=7,column=1)
    win._patient_id = Label(win,text="Patient ID").grid(row=8,column=0)
    # win.patient_id = StringVar()
    win.patient_id_e = Entry(win,width=40,textvariable=win.patient_id).grid(row=8,column=1)

    win._study_details = Label(win,text="Study Details").grid(row=9,column=0,columnspan=2)
    win._study_description = Label(win,text="Study Description").grid(row=10,column=0)
    # win.study_description = StringVar()
    win.study_description_e = Entry(win,width=40,textvariable=win.study_description).grid(row=10,column=1)
    win._study_uid = Label(win,text="Study UID").grid(row=11,column=0)
    # win.study_uid = StringVar()
    win.study_uid_e = Entry(win,width=40,textvariable=win.study_uid).grid(row=11,column=1)
    win._accession_number = Label(win,text="Accession Number").grid(row=12,column=0)
    # win.accession_number = StringVar()
    win.accession_number_e = Entry(win,width=40,textvariable=win.accession_number).grid(row=12,column=1)
    win._study_date = Label(win,text="Study Date (DD/MM/YYYY)").grid(row=13,column=0)
    # win.study_date = StringVar()
    win.study_date_e = Entry(win,width=40,textvariable=win.study_date).grid(row=13,column=1)
    win._study_time = Label(win,text="Study Time - 24h clock (hh:mm:ss)").grid(row=14,column=0)
    # win.study_time = StringVar()
    win.study_time_e = Entry(win,width=40,textvariable=win.study_time).grid(row=14,column=1)

    win._series_details = Label(win,text="Series Details").grid(row=15,column=0,columnspan=2)
    win._series_description = Label(win,text="Series Description").grid(row=16,column=0)
    # win.series_description = StringVar()
    win.series_description_e = Entry(win,width=40,textvariable=win.series_description).grid(row=16,column=1)
    win._series_number = Label(win,text="Series Number").grid(row=17,column=0)
    # win.series_number = StringVar()
    win.series_number_e = Entry(win,width=40,textvariable=win.series_number).grid(row=17,column=1)
    win._series_uid = Label(win,text="Series UID").grid(row=18,column=0)
    # win.series_uid = StringVar()
    win.series_uid_e = Entry(win,width=40,textvariable=win.series_uid).grid(row=18,column=1)

    win._image_details = Label(win,text="Image Details").grid(row=19,column=0,columnspan=2)
    win._instance_number = Label(win,text="Instance Number").grid(row=20,column=0)
    # win.instance_number = StringVar()
    win.instance_number = Entry(win,width=40)#,textvariable=win.instance_number)
    win.instance_number.grid(row=20,column=1)
    win._instance_uid = Label(win,text="Instance UID").grid(row=21,column=0)
    # win.instance_uid = StringVar()
    win.instance_uid = Entry(win,width=40)#,textvariable=win.instance_uid)
    win.instance_uid.grid(row=21,column=1)

    win._button_frame = Frame(win)
    win._apply = Button(win._button_frame,text="Apply Changes",command=lambda:apply_changes(win))
    win._apply.grid(row=0,column=0,sticky='nsew')
    win._cancel = Button(win._button_frame,text="Cancel",command=lambda:close_window(win))
    win._cancel.grid(row=0,column=1,sticky='nsew')

    win._button_frame.grid(row=22,column=0,columnspan=2)

    return

def get_details(win):
    # Check length of loaded image series
    # If multiple images - disable image details
    # If multiple series - disable series details
    # If multiple studies - do nothing

    if len(win.images)==1:
        # Single series
        ds = pydicom.dcmread(win.images[0][0])
        if len(win.images[0])==1:
            # Single image- collect image details
            win.instance_uid.insert(0,ds.SOPInstanceUID)
            win.instance_number.insert(0,ds.InstanceNumber)
        else:
            # Multiple images - disable image details
            win.instance_uid.config(state='disabled')
            win.instance_number.config(state='disabled')
        # Collect series details
