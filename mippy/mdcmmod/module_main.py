from tkinter import *
# from tkinter.ttk import *
import tkinter.messagebox
from mippy.viewing import *
import os
from PIL import Image,ImageTk
import platform
from pkg_resources import resource_filename
from contextlib import suppress

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
    win.patient_details = []
    win._family_name = Label(win,text="Family Name").grid(row=1,column=0)
    win.family_name = Entry(win,width=60)
    win.patient_details.append(win.family_name)
    win.family_name.grid(row=1,column=1)
    win._given_name = Label(win,text="Given Name").grid(row=2,column=0)
    win.given_name = Entry(win,width=60)
    win.patient_details.append(win.given_name)
    win.given_name.grid(row=2,column=1)
    win._middle_name = Label(win,text="Middle Name").grid(row=3,column=0)
    win.middle_name = Entry(win,width=60)
    win.patient_details.append(win.middle_name)
    win.middle_name.grid(row=3,column=1)
    win._patient_title = Label(win,text="Title").grid(row=4,column=0)
    win.patient_title = Entry(win,width=60)
    win.patient_details.append(win.patient_title)
    win.patient_title.grid(row=4,column=1)
    win._suffix = Label(win,text="Suffix").grid(row=5,column=0)
    win.suffix = Entry(win,width=60)
    win.patient_details.append(win.suffix)
    win.suffix.grid(row=5,column=1)
    win._phonetic = Label(win,text="Phonetic Name").grid(row=6,column=0)
    win.phonetic = Entry(win,width=60)
    win.patient_details.append(win.phonetic)
    win.phonetic.grid(row=6,column=1)
    win._dob = Label(win,text="Date of Birth (DD/MM/YYYY)").grid(row=7,column=0)
    win.dob = Entry(win,width=60)
    win.patient_details.append(win.dob)
    win.dob.grid(row=7,column=1)
    win._patient_id = Label(win,text="Patient ID").grid(row=8,column=0)
    win.patient_id = Entry(win,width=60)
    win.patient_details.append(win.patient_id)
    win.patient_id.grid(row=8,column=1)

    win._study_details = Label(win,text="Study Details").grid(row=9,column=0,columnspan=2)
    win.study_details = []
    win._study_description = Label(win,text="Study Description").grid(row=10,column=0)
    win.study_description = Entry(win,width=60)
    win.study_details.append(win.study_description)
    win.study_description.grid(row=10,column=1)
    win._study_uid = Label(win,text="Study UID").grid(row=11,column=0)
    win.study_uid = Entry(win,width=60)
    win.study_details.append(win.study_uid)
    win.study_uid.grid(row=11,column=1)
    win._accession_number = Label(win,text="Accession Number").grid(row=12,column=0)
    win.accession_number = Entry(win,width=60)
    win.study_details.append(win.accession_number)
    win.accession_number.grid(row=12,column=1)
    win._study_date = Label(win,text="Study Date (DD/MM/YYYY)").grid(row=13,column=0)
    win.study_date = Entry(win,width=60)
    win.study_details.append(win.study_date)
    win.study_date.grid(row=13,column=1)
    win._study_time = Label(win,text="Study Time - 24h clock (hh:mm:ss)").grid(row=14,column=0)
    win.study_time = Entry(win,width=60)
    win.study_details.append(win.study_time)
    win.study_time.grid(row=14,column=1)

    win._series_details = Label(win,text="Series Details").grid(row=15,column=0,columnspan=2)
    win.series_details = []
    win._series_description = Label(win,text="Series Description").grid(row=16,column=0)
    win.series_description = Entry(win,width=60)
    win.series_details.append(win.series_description)
    win.series_description.grid(row=16,column=1)
    win._series_number = Label(win,text="Series Number").grid(row=17,column=0)
    win.series_number = Entry(win,width=60)
    win.series_details.append(win.series_number)
    win.series_number.grid(row=17,column=1)
    win._series_uid = Label(win,text="Series UID").grid(row=18,column=0)
    win.series_uid = Entry(win,width=60)
    win.series_details.append(win.series_uid)
    win.series_uid.grid(row=18,column=1)

    win._image_details = Label(win,text="Image Details").grid(row=19,column=0,columnspan=2)
    win.image_details = []
    win._instance_number = Label(win,text="Instance Number").grid(row=20,column=0)
    win.instance_number = Entry(win,width=60)
    win.image_details.append(win.instance_number)
    win.instance_number.grid(row=20,column=1)
    win._instance_uid = Label(win,text="Instance UID").grid(row=21,column=0)
    win.instance_uid = Entry(win,width=60)
    win.image_details.append(win.instance_uid)
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

    ds = pydicom.dcmread(win.images[0][0])

    if len(win.images)==1:
        # Single series
        if len(win.images[0])==1:
            # Single image- collect image details
            win.instance_uid.insert(0,ds.SOPInstanceUID)
            win.instance_number.insert(0,ds.InstanceNumber)
        else:
            # Multiple images - disable image details
            for w in win.image_details:
                w.config(state='disabled')
        # Collect series details
        win.series_description.insert(0,ds.SeriesDescription)
        win.series_number.insert(0,ds.SeriesNumber)
        win.series_uid.insert(0,ds.SeriesInstanceUID)
    else:
        # Multiple series - disable series details and image details
        for w in win.series_details:
            w.config(state='disabled')
        for w in win.image_details:
            w.config(state='disabled')

        # Check for images from different studies
        study_uids = []
        for series in win.images:
            this_uid = pydicom.dcmread(series[0]).StudyInstanceUID
            if not this_uid in study_uids:
                study_uids.append(this_uid)
        if len(study_uids)>1:
            tkinter.messagebox.showerror(title="Multiple studies loaded", message="This module can only be used on images from a single study")
            close_window()

    # If you've got this far, continue on to study and patient details
    with suppress(AttributeError):
        win.study_description.insert(0,ds.StudyDescription)
    with suppress(AttributeError):
        win.study_uid.insert(0,ds.StudyInstanceUID)
    with suppress(AttributeError):
        win.accession_number.insert(0,ds.AccessionNumber)
    with suppress(AttributeError):
        win.study_date.insert(0,ds.StudyDate)
    with suppress(AttributeError):
        win.study_time.insert(0,ds.StudyTime)

    with suppress(AttributeError):
        win.family_name.insert(0,ds.PatientName.family_name)
    with suppress(AttributeError):
        win.given_name.insert(0,ds.PatientName.given_name)
    with suppress(AttributeError):
        win.middle_name.insert(0,ds.PatientName.middle_name)
    with suppress(AttributeError):
        win.patient_title.insert(0,ds.PatientName.name_prefix)
    with suppress(AttributeError):
        win.suffix.insert(0,ds.PatientName.name_suffix)
    with suppress(AttributeError):
        win.phonetic.insert(0,ds.PatientName.phonetic)
    with suppress(AttributeError):
        win.dob.insert(0,ds.PatientBirthDate)
    with suppress(AttributeError):
        win.patient_id.insert(0,ds.PatientID)
