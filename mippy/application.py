"""
###########################
MIPPY: Modular Image Processing in Python
###########################
mippy.application
Author: Robert Flintham

This file contains MIPPY's main "Application" class. This defines the main
DICOM browser window, and what each of the menu options/buttons etc
all do.
"""

# Import system/python modules
#~ print "Importing system modules"
from pkg_resources import resource_filename
import os
import tkinter.messagebox
import tkinter.filedialog
from tkinter import *
from tkinter.ttk import *
#~ import ScrolledText
from datetime import datetime
import sys
import numpy as np
import time
import webbrowser
import shutil
import importlib
import getpass
import pickle as pickle
import itertools
from functools import partial
import stat
import pydicom
import gc
#~ from multiprocessing import freeze_support
#~ print "Imports finished!"

#~ print "Importing MIPPY code"
from . import viewing as mview
from . import mdicom
from .mdicom.reading import collect_dicomdir_info
from .mdicom.reading import get_dataset
from .mdicom.reading import compare_dicom
from .mdicom.reading import load_images_from_uids
from .mdicom.mrenhanced import get_frame_ds
from .mdicom.io import save_temp_ds
from . import fileio
from .threading import multithread
import imp
#~ print "Done!"
from zipfile import ZipFile

# WEB LINKS
MIPPYDOCS = r'http://mippy.readthedocs.io'
    

class MIPPYMain(Frame):

    ## Define any global attributes/variables you'll need here.  Use as few of these
    ## as possible as they will exist in RAM for as long as the program is running
    ## and are a waste of memory if they're not needed.  They also create massive
    ## confusion if you want to use similar/the same variable names in other modules






    def __init__(self, master):
        """
        This is the function which is called automatically when you create an object of
        this class, to initiate ("init", get it?) the object.

        This is where the GUI is first created and populated with buttons, image canvasses,
        tabs, whatever.  This function can also call other functions should you wish to split
        the code down further.
        """
        
        # IMPORT STATEMENTS - THESE ARE NOT CALLED UNTIL THE APPLICATION IS STARTED
        
        
        
        self.root_dir = os.getcwd()
        self.dicomdir = None

        # Initialises the GUI as a "Frame" object and gives it the name "master"
        Frame.__init__(self, master)
        self.master = master
        self.master.root_dir = os.getcwd()
        self.master.title("MIPPY: Modular Image Processing in Python")
        #~ self.master.minsize(650,400)
        #~ self.root_path = os.getcwd()
        
        
        
        if "nt" == os.name:
            impath = resource_filename('mippy','resources/brain_orange.ico')
        else:
            impath = '@'+resource_filename('mippy','resources/brain_bw.xbm')
        self.master.wm_iconbitmap(impath)

        # Catches any calls to close the window (e.g. clicking the X button in Windows) and pops
        # up an "Are you sure?" dialog
        self.master.protocol("WM_DELETE_WINDOW", self.asktoexit)



        


        

        '''
        This section is to determine the host OS, and set up the appropriate temp
        directory for images.
        Windows = C:\Temp
        Mac = /tmp
        Linux = /tmp
        '''
        
        # Use parallel processing?
        self.multiprocess = True
        
        self.user = getpass.getuser()
        
        
        import pkg_resources
        import sys
        if sys.argv[0]=='mippydev.py':
            self.mippy_version = "DEVELOPMENT_VERSION"
        else:
            self.mippy_version = pkg_resources.get_distribution("mippy").version
        
        # Set temp directory
        if 'darwin' in sys.platform or 'linux' in sys.platform:
            self.tempdir = '/tmp/MIPPY_temp_'+self.user            
        elif 'win' in sys.platform:
            fallback_temp = r'C:\TEMP'
            sys_temp  = os.getenv("TEMP",fallback_temp)
            
            # If sys_temp not accessible, default to fallback_temp
            if not os.access(sys_temp, os.W_OK):
                sys_temp = fallback_temp
                print("System reported temp directory not available - using {}".format(sys_temp))
            
            self.tempdir = os.path.join(sys_temp,"MIPPY_temp_"+self.user)
        else:
            tkinter.messagebox.showerror('ERROR', 'Unsupported operating system, please contact the developers.')
            sys.exit()
        if not os.path.exists(self.tempdir):
            os.makedirs(self.tempdir)
        
        # Set persistent user directory
        self.fallback_userdir = None
        self.userdir = None
        if 'darwin' in sys.platform or 'linux' in sys.platform:
            #~ self.userdir = os.path.join('/home',self.user,'.mippy')
            self.userdir = os.path.expanduser('~/.mippy')
        elif 'win' in sys.platform:
            fallback_sys_userdir = os.path.join(r'C:\Users',self.user)
            sys_userdir = os.getenv('APPDATA',fallback_sys_userdir)
            
            # If sys_userdir not available, default to fallback_userdir
            if not os.access(sys_userdir, os.W_OK):
                sys_userdir = fallback_sys_userdir
                print("System reported user directory not available - using {}".format(sys_userdir))
            
            self.userdir = os.path.join(sys_userdir,'.mippy')
            self.fallback_userdir = os.path.join(fallback_sys_userdir,'.mippy')
        else:
            tkinter.messagebox.showerror('ERROR', 'Unsupported operating system, please contact the developers.')
            sys.exit()
        
        if not os.path.exists(self.userdir):
            os.makedirs(self.userdir)
        
        # If newer files in fallback directory than system reported directory, update files
        if ('win' in sys.platform
            and not 'darwin' in sys.platform
            and os.path.exists(self.fallback_userdir)
            and not self.fallback_userdir==self.userdir):
            files_updated = fileio.copyToDir(self.fallback_userdir,self.userdir)
            if len(files_updated)>0:
                print("The following fles have been updated in your home directory:")
                for f in files_updated:
                        print("- {}".format(f))
        
        # Set default module directory
        if os.path.exists(os.path.join(self.userdir,'defaultmodulepath.txt')):
            with open(os.path.join(self.userdir,'defaultmodulepath.txt'),'r') as modpathfile:
                requested_moduledir = modpathfile.readlines()[0].lstrip().rstrip()
                if os.path.exists(requested_moduledir):
                    self.moduledir = requested_moduledir
                    print('USING MODULE DIRECTORY: {}'.format(self.moduledir))
        elif os.path.exists(os.path.join(self.root_dir, 'modules')):
            self.moduledir = os.path.join(self.root_dir, 'modules')
            if not self.moduledir in sys.path:
                sys.path.append(self.moduledir)
        else:
            self.moduledir = None
        
        # Create a list to hold module eggs
        self.module_eggs = []
        
        # Create variable for export directory
        self.exportdir = None
        
        # Check status of DCMDJPEG for mac or unix, and set
        # executable if necessary
        
        # Create "working copy" of the correct DCMDJPEG in the temp folder and
        # set executable flag as necessary
        
        if 'darwin' in sys.platform:
            dcmdjpegpath = resource_filename('mippy','resources/dcmdjpeg_mac')
        elif 'linux' in sys.platform:
            dcmdjpegpath = resource_filename('mippy','resources/dcmdjpeg_linux')
        elif 'win' in sys.platform:
            dcmdjpegpath = resource_filename('mippy','resources/dcmdjpeg_win.exe')
        
        dcmdjpeg_copy = os.path.join(self.tempdir,os.path.split(dcmdjpegpath)[1])
        
        shutil.copy(dcmdjpegpath,dcmdjpeg_copy)
        
        #~ print os.stat(dcmdjpeg_copy)
        
        if 'darwin' in sys.platform or 'linux' in sys.platform:
            st = os.stat(dcmdjpeg_copy)
            os.chmod(dcmdjpeg_copy,st.st_mode | stat.S_IEXEC)

        ## Change ttk theme on linux

        if 'darwin' in sys.platform:
            pass
        elif 'linux' in sys.platform:
            s = Style()
            s.theme_use('default')
        elif 'win' in sys.platform:
            dcmdjpegpath = resource_filename('mippy','resources/dcmdjpeg_win.exe')

        # Create menu bar for the top of the window
        self.menubar = Menu(master)
        # Create and populate "File" menu
        self.filemenu = Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Load new image directory", command=lambda:self.load_image_directory())
        self.filemenu.add_command(label="Open user home directory", command=lambda:self.open_user_directory())
        self.filemenu.add_command(label="Exit program",command=lambda:self.exit_program())
        # Create and populate "Modules" menu
        self.modulemenu = Menu(self.menubar,tearoff=0)
        self.modulemenu.add_command(label="Load new module directory",command=lambda:self.select_modules_directory())
        self.modulemenu.add_command(label="Refresh module list", command=lambda:self.scan_modules_directory())
        # Create and populate "Image" menu
        self.imagemenu = Menu(self.menubar,tearoff=0)
        self.imagemenu.add_command(label="View DICOM header", command=lambda:self.view_header())
        self.imagemenu.add_command(label="Compare DICOM headers", command=lambda:self.compare_headers())
        self.imagemenu.add_command(label="Export DICOM files", command=lambda:self.export_dicom())
        # Create and populate "Options" menu
        self.optionsmenu = Menu(self.menubar,tearoff=0)
        self.optionsmenu.add_command(label="Enable multiprocessing", command=lambda:self.enable_multiprocessing())
        self.optionsmenu.add_command(label="Disable multiprocessing", command=lambda:self.disable_multiprocessing())
        # Create and populate "Help" menu
        self.helpmenu = Menu(self.menubar, tearoff=0)
        self.helpmenu.add_command(label="Open MIPPY documentation",command=lambda:self.load_docs())
        self.helpmenu.add_command(label="About MIPPY",command=lambda:self.display_version_info())
        #~ self.helpmenu.add_command(label="View changelog",command=lambda:self.display_changelog())
        self.helpmenu.add_command(label="Report issue",command=lambda:self.report_issue())
        #~ self.helpmenu.add_command(label="View current log file",command=lambda:self.show_log())
        # Add menus to menubar and display menubar in window
        self.menubar.add_cascade(label="File",menu=self.filemenu)
        self.menubar.add_cascade(label="Modules",menu=self.modulemenu)
        self.menubar.add_cascade(label="Image",menu=self.imagemenu)
        self.menubar.add_cascade(label="Options",menu=self.optionsmenu)
        self.menubar.add_cascade(label="Help",menu=self.helpmenu)
        self.master.config(menu=self.menubar)

        # Create frames to hold DICOM directory tree and module list
        self.dirframe = Frame(self.master)
        self.moduleframe = Frame(self.master)
        self.dirframe = Frame(self.master)
        self.moduleframe = Frame(self.master)

        # Create DICOM treeview
        self.dirframe.dicomtree = Treeview(self.dirframe)

        # Set names and widths of columns in treeviews
        self.dirframe.dicomtree['columns']=('date','name','desc')
        self.dirframe.dicomtree.heading('date',text='Study Date')
        self.dirframe.dicomtree.heading('name',text='Patient Name')
        self.dirframe.dicomtree.heading('desc',text='Description')
        self.dirframe.dicomtree.column('#0',width=100,stretch=False)
        self.dirframe.dicomtree.column('date',width=100,stretch=False)
        self.dirframe.dicomtree.column('name',width=200)
        self.dirframe.dicomtree.column('desc',width=500)

        # Create scrollbars
        self.dirframe.scrollbarx = Scrollbar(self.dirframe,orient='horizontal')
        self.dirframe.scrollbarx.config(command=self.dirframe.dicomtree.xview)
        self.dirframe.scrollbary = Scrollbar(self.dirframe)
        self.dirframe.scrollbary.config(command=self.dirframe.dicomtree.yview)
        self.dirframe.dicomtree.configure(yscroll=self.dirframe.scrollbary.set, xscroll=self.dirframe.scrollbarx.set)

        # Use "grid" to postion treeview and scrollbars in DICOM frame and assign weights to columns and rows
        self.dirframe.dicomtree.grid(row=0,column=0,sticky='nsew')
        self.dirframe.scrollbarx.grid(row=1,column=0,sticky='nsew')
        self.dirframe.scrollbary.grid(row=0,column=1,sticky='nsew')

        # Set "weights" (relatve amount of stretchability when resizing window) for each row and column
        self.dirframe.rowconfigure(0,weight=1)
        self.dirframe.columnconfigure(0,weight=1)
        self.dirframe.rowconfigure(1,weight=0)
        self.dirframe.columnconfigure(1,weight=0)

        # Bind "change selection" event to method to update the image display
        self.dirframe.dicomtree.bind('<<TreeviewSelect>>',self.dir_window_selection)

        # Remove focus from dicomtree widget when mouse not hovering
        #~ self.master.dirframe.dicomtree.bind('<Leave>',self.dicomtree_nofocus)
        #~ self.master.dirframe.dicomtree.bind('<Enter>',self.dicomtree_focus)


        # Create module treeview
        self.moduleframe.moduletree = Treeview(self.moduleframe)

        # Set names and widths of columns in treeview
        self.moduleframe.moduletree['columns']=('description','author','version')
        self.moduleframe.moduletree.heading('#0',text='Module Name')
        self.moduleframe.moduletree.heading('description',text='Description')
        self.moduleframe.moduletree.heading('author',text='Author')
        self.moduleframe.moduletree.heading('version',text='Version')

        # Create scrollbars
        self.moduleframe.scrollbarx = Scrollbar(self.moduleframe,orient='horizontal')
        self.moduleframe.scrollbarx.config(command=self.moduleframe.moduletree.xview)
        self.moduleframe.scrollbary = Scrollbar(self.moduleframe)
        self.moduleframe.scrollbary.config(command=self.moduleframe.moduletree.yview)
        self.moduleframe.moduletree.configure(yscroll=self.moduleframe.scrollbary.set, xscroll=self.moduleframe.scrollbarx.set)

        # Use "grid" to postion treeview and scrollbars in DICOM frame and assign weights to columns and rows
        self.moduleframe.moduletree.grid(row=0,column=0,sticky='nsew')
        self.moduleframe.scrollbarx.grid(row=1,column=0,sticky='nsew')
        self.moduleframe.scrollbary.grid(row=0,column=1,sticky='nsew')

        # Set "weights" (relatve amount of stretchability when resizing window) for each row and column
        self.moduleframe.rowconfigure(0,weight=1)
        self.moduleframe.columnconfigure(0,weight=1)
        self.moduleframe.rowconfigure(1,weight=0)
        self.moduleframe.columnconfigure(1,weight=0)

        # Remove focus from moduletree widget when mouse not hovering
        #~ self.master.moduleframe.moduletree.bind('<Leave>',self.moduletree_nofocus)
        #~ self.master.moduleframe.moduletree.bind('<Enter>',self.moduletree_focus)

        # Load modules to list
        self.scan_modules_directory()
        # TEMPORARILY DISABLED

        # Bind "module select" event to required action
        self.moduleframe.moduletree.bind('<<TreeviewSelect>>',self.module_window_click)

        # Just adding a random line to the tree for testing
        #self.master.moduleframe.moduletree.insert('','end',"test row",text="Blah blah",values=("Option 1","Option 2"))

        # Create canvas object to draw images in
        self.imcanvas = mview.MIPPYCanvas(self.master,bd=0,width=256, height=256,drawing_enabled=False)


        # Add a scrollbar to MIPPYCanvas to enable slice scrolling
        self.imcanvas.img_scrollbar = Scrollbar(self.master,orient='horizontal')
        self.imcanvas.configure_scrollbar()

        # Create buttons:
        # "Load module"
        self.loadmodulebutton = Button(self.master,text="Load module",command=lambda:self.load_selected_module())

        # Add progressbar
        self.master.progressbar = Progressbar(self.master, mode='determinate')

        # Use "grid" to position objects within "master"
        self.dirframe.grid(row=0,column=0,columnspan=2,rowspan=1,sticky='nsew')
        self.imcanvas.grid(row=1,column=0,sticky='nsew')
        self.moduleframe.grid(row=1,column=1,sticky='nsew')
        self.loadmodulebutton.grid(row=2,column=1,sticky='nsew')
        #~ self.scrollbutton.grid(row=2,column=0,sticky='nsew')
        self.imcanvas.img_scrollbar.grid(row=2,column=0,sticky='ew')
        self.master.progressbar.grid(row=3,column=0,rowspan=1,columnspan=2,sticky='nsew')

        # Set row and column weights to handle resizing
        self.master.rowconfigure(0,weight=1)
        self.master.rowconfigure(1,weight=0)
        self.master.rowconfigure(2,weight=0)
        self.master.rowconfigure(3,weight=0)
        self.master.columnconfigure(0,weight=0)
        self.master.columnconfigure(1,weight=1)

        self.focus()

        # Here are some variables that may be useful
        self.open_ds = None
        self.open_file = None

    def slice_scroll_button_click(self,event):
        self.click_x = event.x
        self.click_y = event.y
        #~ print "CLICK"
        return
    
    def open_user_directory(self):
        webbrowser.open(self.userdir)
        return




    def asktoexit(self):
#        if tkMessageBox.askokcancel("Quit?", "Are you sure you want to exit?"):
#            self.master.destroy()
            #~ sys.exit()
        mbox = tkinter.messagebox.Message(
            title='Delete temporary files?',
            message='Would you like to delete all MIPPY temp files?',
            icon=tkinter.messagebox.QUESTION,
            type=tkinter.messagebox.YESNOCANCEL,
            master = self)
        reply = mbox.show()
        if reply=='yes':
            self.clear_temp_dir()
            self.master.destroy()
        elif reply=='no':
            self.master.destroy()
        else:
            return
        return



    def dir_window_selection(self,event):
        # THIS NEEDS IF len==1 to decide how to draw preview images
        selection = self.dirframe.dicomtree.selection()
        self.active_uids = []
        for item in selection:
            parent_item = self.dirframe.dicomtree.parent(item)
            if parent_item=='':
                # Whole study, not sure what to do...
                self.imcanvas.reset()
                #~ print "Whole study selected, no action determined yet."
            elif self.dirframe.dicomtree.parent(parent_item)=='':
                # Whole series, add children to list
                for image_uid in self.dirframe.dicomtree.get_children(item):
                    self.active_uids.append(image_uid)
                if len(selection)==1:
                    if not item==self.active_series:
                        self.load_preview_images(self.dirframe.dicomtree.get_children(item))
                        self.active_series = item
                    self.imcanvas.show_image(1)
            else:
                # Single slice
                self.active_uids.append(item)
                if len(selection)==1:
                    parent = self.dirframe.dicomtree.parent(item)
                    if not parent==self.active_series:
                        self.load_preview_images(self.dirframe.dicomtree.get_children(parent))
                        self.active_series = parent
                    self.imcanvas.show_image(self.dirframe.dicomtree.index(item)+1)

    def progress(self,percentage):
        self.master.progressbar['value']=percentage
        self.master.progressbar.update()

    def load_preview_images(self, uid_array):
        """
        Requires an array of unique instance UID's to search for in self.tag_list
        """
        #~ self.reset_small_canvas()
        n = 0
        preview_images = []
        for tag in self.sorted_list:
            if tag['instanceuid'] in uid_array:
                self.progress(10.*n/len(uid_array))
                preview_images.append(tag['px_array'])
                n+=1
        self.imcanvas.load_images(preview_images)
        return



    def module_window_click(self,event):
        print("You clicked on the module window.")

    def load_image_directory(self):
        print("Load image directory")
        prev_dir = self.dicomdir
        try:
            # Unpickle previous directory if available
            with open(os.path.join(self.userdir,'prevdir.cfg'),'rb') as cfg_file:
                prevdir = pickle.load(cfg_file)
            print("PREV DIRECTORY: {}".format(prevdir))
        except:
            prevdir = None
        self.dicomdir = tkinter.filedialog.askdirectory(parent=self,initialdir=prevdir,title="Select image directory")
        if not self.dicomdir:
            self.dicomdir = prev_dir
            return
        with open(os.path.join(self.userdir,'prevdir.cfg'),'wb') as cfg_file:
            pickle.dump(self.dicomdir,cfg_file)
        self.ask_recursive = tkinter.messagebox.askyesno("Search recursively?","Do you want to include all subdirectories?")

        #~ self.path_list = []
        self.active_series = None
        
        # Check for appropriate mippydb object in the chosen directory
        if self.ask_recursive:
            self.mippydbpath = os.path.join(self.dicomdir,"mippydb_r")
        else:
            self.mippydbpath = os.path.join(self.dicomdir,"mippydb")
        if os.path.exists(self.mippydbpath):
            ask_use_mippydb = tkinter.messagebox.askyesno("Load existing MIPPYDB?","MIPPYDB file found. Load the existing DICOM tree?")
            if ask_use_mippydb:
                with open(self.mippydbpath,'rb') as fileobj:
                    self.sorted_list = pickle.load(fileobj)
                self.tag_list = self.sorted_list    # Shouldn't need this really...
                self.build_dicom_tree()
                return

        self.path_list = fileio.list_all_files(self.dicomdir,recursive=self.ask_recursive)

        self.filter_dicom_files()
        self.build_dicom_tree()

        return

    def filter_dicom_files(self):
        self.tag_list = []
        
        if self.multiprocess and not (('win' in sys.platform and not 'darwin' in sys.platform)
                                and len(self.path_list)<20):
            f = partial(collect_dicomdir_info,tempdir=self.tempdir)
            self.tag_list = multithread(f,self.path_list,progressbar=self.progress)
            self.tag_list = [item for sublist in self.tag_list for item in sublist]
            self.tag_list = [value for value in self.tag_list if value != []]
        else:
            for p in self.path_list:
                self.progress(100*(float(self.path_list.index(p))/float(len(self.path_list))))
                tags = collect_dicomdir_info(p,tempdir=self.tempdir)
                if not tags is None:
                    for row in tags:
                        self.tag_list.append(row)
            self.progress(0.)
        # This should sort the list into your initial order for the tree - maybe implement a more customised sort if necessary?
        from operator import itemgetter
        self.sorted_list = sorted(self.tag_list, key=itemgetter('name','date','time','studyuid','series','seriesuid','instance','instanceuid'))
        
        # Uncomment this block to enable mippydb objects in image directory
        #~ if self.ask_recursive:
            #~ self.mippydbpath = os.path.join(self.dicomdir,"mippydb_r")
        #~ else:
            #~ self.mippydbpath = os.path.join(self.dicomdir,"mippydb")
        #~ with open(self.mippydbpath,'wb') as fileobj:
            #~ pickle.dump(self.sorted_list,fileobj,-1)

        return

    def build_dicom_tree(self):
        #~ print "function_started"
        #~ i=0
        print(self.dirframe.dicomtree.get_children())
        try:
            for item in self.dirframe.dicomtree.get_children():
                self.dirframe.dicomtree.delete(item)
            print("Existing tree cleared")
        except Exception:
            print("New tree created")
            pass
        repeats_found = False
        n_repeats = 0
        for scan in self.sorted_list:
            #~ print "Adding to tree: "+scan['path']
            if not self.dirframe.dicomtree.exists(scan['studyuid']):
                #~ i+=1
                self.dirframe.dicomtree.insert('','end',scan['studyuid'],text='------',
                                                values=(scan['date'],scan['name'],scan['studydesc']))
            if not self.dirframe.dicomtree.exists(scan['seriesuid']):
                self.dirframe.dicomtree.insert(scan['studyuid'],'end',scan['seriesuid'],
                                            text='Series '+str(scan['series']).zfill(3),
                                            values=('','',scan['seriesdesc']))
            try:
                self.dirframe.dicomtree.insert(scan['seriesuid'],'end',scan['instanceuid'],
                                        text=str(scan['instance']).zfill(3),
                                        values=('','',''))
            except:
                repeats_found = True
                n_repeats+=1
        if repeats_found:
            tkinter.messagebox.showwarning("WARNING",str(n_repeats)+" repeat image UID's found and ignored.")
        self.dirframe.dicomtree.update()
        
        # Run garbage collect to clear anything left in memory unnecessarily
        gc.collect()

        # Save DICOM tree as a snapshot to be opened again at a later time


        #~ self.master.progress = 100
        return
    
    def select_modules_directory(self):
        print("Load module directory")
        if self.moduledir in sys.path:
            sys.path.remove(self.moduledir)
        for eggpath in self.module_eggs:
            if eggpath in sys.path:
                sys.path.remove(eggpath)
                
        for line in sys.path:
            print(line)
        
        # Grab existing module directory to put back if dialog is cancelled
        prev_mod_dir = self.moduledir
        
        self.moduledir = None
        self.moduledir = tkinter.filedialog.askdirectory(parent=self,initialdir=self.root_dir,title="Select module directory")
        if not self.moduledir:
            self.moduledir = prev_mod_dir
            return
#        sys.path.append(self.moduledir)
        self.scan_modules_directory()
        return        

    def scan_modules_directory(self):
        self.module_list = []
        self.module_eggs = []
        viewerconfigpath = resource_filename('mippy.mviewer','config')
        with open(viewerconfigpath,'rb') as file_object:
            module_info = pickle.load(file_object)
        module_info['dirname']='mippy.mviewer'
        module_info['version']=''
        module_info['eggpath']=None
        self.module_list.append(module_info)
        
        
        if not (self.moduledir is None or not self.moduledir):
            for folder in os.listdir(self.moduledir):
                if not os.path.isdir(os.path.join(self.moduledir,folder)):
                    # Might be an egg.  Try and read as an egg...
                    if folder.upper().endswith('.EGG'):
                        print("{}: It's an egg!!".format(folder))
                        
                        # Get the properties of the egg
                        this_eggpath = os.path.join(self.moduledir,folder)
                        with ZipFile(this_eggpath, 'r') as modulezip:
                            dirs = []
                            pkg_info = {}
                            with modulezip.open('EGG-INFO/PKG-INFO', 'r') as pkg_info_file:
                                for row in pkg_info_file.readlines():
                                    info = row.decode('utf-8').split(':')
                                    if len(info)==2:
                                        pkg_info[info[0]]=info[1].rstrip().lstrip()
                                # print(pkg_info['Name'],pkg_info['Version'])
                                with modulezip.open('EGG-INFO/top_level.txt', 'r') as toplevel:
                                    for row in toplevel.readlines():
                                        dirs.append(row.decode('utf-8').rstrip().lstrip())
                                    for zipdir in dirs:
                                        # Whether config exists or not, need to remove any reference
                                        # to previously loaded modules of these names
                                        to_remove = []
                                        for mod in sys.modules:
                                            if zipdir in mod:
                                                print("Existing module found! {}".format(mod))
                                                to_remove.append(mod)
                                        for mod in to_remove:
                                            sys.modules.pop(mod)
                                        gc.collect()
                                        cfg_file = zipdir+'/config'
                                        if cfg_file in modulezip.namelist():
                                            print(zipdir, "exists")
                                            if not this_eggpath in self.module_eggs:
                                                self.module_eggs.append(this_eggpath)
#                                            if not this_eggpath in sys.path:
#                                                sys.path.append(this_eggpath)
#                                                print(sys.path[-1])
                                            with modulezip.open(cfg_file,'r') as file_object:
                                                module_info = pickle.load(file_object)
                                                # module_info['dirname']=pkg_info['Name']+'.'+module_info['dirname']
                                                module_info['version'] = pkg_info['Version']
                                                module_info['eggpath'] = this_eggpath
                                                
                                                ## CHECK HERE FOR VERSION CLASH
                                                ##
                                                ##
                                                for mod in self.module_list:
                                                    if (module_info['dirname']==mod['dirname'] and
                                                        module_info['version']==mod['version']):
                                                        print("MODULE CLASH: {} {}".format(module_info['dirname'],module_info['version']))
                                                        self.module_list = []
                                                        return
                                                
                                                
                                                self.module_list.append(module_info)
                                        
                        continue
                    else:
                        continue
                file_list = os.listdir(os.path.join(self.moduledir,folder))
                if (('__init__.py' in file_list or '__init__.pyc' in file_list)
                    and ('module_main.py' in file_list or 'module_main.pyc' in file_list)
                    and 'config' in file_list):
                    # Whether config exists or not, need to remove any reference
                    # to previously loaded modules of these names
                    to_remove = []
                    for mod in sys.modules:
                        if folder in mod:
                            print("Existing module found! {}".format(mod))
                            to_remove.append(mod)
                    for mod in to_remove:
                        sys.modules.pop(mod)
                    gc.collect()
                    cfg_file = os.path.join(self.moduledir,folder,'config')
                    with open(cfg_file,'rb') as file_object:
                        module_info = pickle.load(file_object)
                        module_info['version']='--uncontrolled--'
                        module_info['eggpath']=None
                        ## CHECK HERE FOR VERSION CLASH
                        ##
                        ##
                        for mod in self.module_list:
                            if (module_info['dirname']==mod['dirname'] and
                                module_info['version']==mod['version']):
                                print("MODULE CLASH: {} {}".format(module_info['dirname'],module_info['version']))
                                self.module_list = []
                                return
                            
                        self.module_list.append(module_info)
            from operator import itemgetter
            self.module_list = sorted(self.module_list,key=itemgetter('version'),reverse=True)
            self.module_list = sorted(self.module_list,key=itemgetter('name'))
        
        try:
            for item in self.moduleframe.moduletree.get_children():
                self.moduleframe.moduletree.delete(item)
            print("Existing module tree cleared")
        except Exception:
            print("New module tree created")
            pass
        for module in self.module_list:
            self.moduleframe.moduletree.insert('','end',module['dirname']+'^'+module['version'],
                text=module['name'],values=(module['description'],module['author'],module['version']))

        #~ self.master.progress = 50.
        
#        for mod in sys.modules:
#            print(mod)
        return

    def exit_program(self):
        self.asktoexit()
        return

    def load_docs(self):
        print("Open documentation")
        webbrowser.open_new(MIPPYDOCS)
        return
    
    def report_issue(self):
        print("Report issue")
        #~ tkinter.messagebox.showinfo("Issue reporting",'Please include the title of your issue in the subject, and a description in the body of the email.\n\n'+
                            #~ 'Where possible, please attach the appropriate log file from MIPPY/logs. Log files are date/time stamped.')
        webbrowser.open_new('https://tree.taiga.io/project/robflintham-mippy/issues')
        return

    def display_version_info(self):
        print("Display version info")
        info = ""
##        verpath = resource_filename('mippy','resources/version.info')
##        with open(verpath,'rb') as infofile:
##            info = infofile.read()
        #~ import mippy
        #~ version = mippy.__version__
        #~ if 'b' in version:
            #~ testing = '(BETA TESTING VERSION)'
        #~ elif 'a' in version:
            #~ testing = '(ALPHA TESTING VERSION)'
        #~ elif 'rc' in version:
            #~ testing = '(Release candidate version)'
        #~ else:
            #~ testing=''
        #~ info = 'Version '+version+'\n'+testing
        from subprocess import Popen,PIPE,check_output
        output = check_output(['pip','show','mippy'])
        info = output
        tkinter.messagebox.showinfo("MIPPY: Version info",info)
        return
    
    def display_changelog(self):
        """
        This has been removed for the time being.
        """
        print("Display changelog")
        info = ""
        with open('docs/changelog.info','rb') as infofile:
            info = infofile.read()
        info_view = Toplevel(self.master)
        info_view.text = Text(info_view,width=120,height=30)
        info_view.text.insert(END,info)
        info_view.text.config(state='disabled')
        info_view.text.see('1.0')
        info_view.text.pack()

    def load_selected_module(self):
        # Remove any existing/leftover paths from sys.path
        if self.moduledir in sys.path:
            sys.path.remove(self.moduledir)
        for eggpath in self.module_eggs:
            if eggpath in sys.path:
                sys.path.remove(eggpath)
        
        # Run a garbage collect to clear anything left over from previous module loading
        gc.collect()
        
        try:
            
            selected_module = self.moduleframe.moduletree.selection()[0]
            moduledir = selected_module.split('^')[0]
            name = self.moduleframe.moduletree.item(selected_module)['text']
            version = self.moduleframe.moduletree.item(selected_module)['values'][2]
            print(name,version)
            module_name = moduledir+'.module_main'
            for mod in self.module_list:
                if moduledir==mod['dirname'] and version==mod['version']:
                    # Update sys.path with the correct values
                    if not mod['eggpath'] is None:
                        sys.path.append(mod['eggpath'])
                    else:
                        sys.path.append(self.moduledir)
        
            # Need to remove any reference
            # to previously loaded modules of this name
            to_remove = []
            for mod in sys.modules:
                if moduledir in mod:
                    to_remove.append(mod)
            for mod in to_remove:
                sys.modules.pop(mod)
                
            active_module = importlib.import_module(module_name)
            imp.reload(active_module)
#            if not module_name in sys.modules:
#                active_module = importlib.import_module(module_name)
#            else:
#                active_module = importlib.import_module(module_name)
#                imp.reload(active_module)
            preload_dicom = active_module.preload_dicom()
            try:
                flatten_list = active_module.flatten_series()
            except:
                message = ("\n\n======================================\n"+
                        "   !!!! MIPPY HAS BEEN UPDATED !!!!\n"+
                        "======================================\n\n"+
                        "Please add a function to your module\n"+
                        "as follows:\n\n"+
                        "def flatten_series():\n"+
                        "    return False\n\n"+
                        "or return True if you require all\n"+
                        "images in a single 1D list.\n"+
                        "======================================\n\n")
                print(message)
                flatten_list = True
            if preload_dicom:
                # Attempted to make this section discrete function for use in modules etc
                self.datasets_to_pass = load_images_from_uids(self.sorted_list,self.active_uids,self.tempdir,self.multiprocess)
                
                
            else:
                self.datasets_to_pass = []
                previous_tag = None
                for tag in self.sorted_list:
                    if previous_tag:
                        if tag['seriesuid']==previous_tag['seriesuid']:
                            new_series = False
                        else:
                            new_series = True
                    else:
                        new_series = True
                    if tag['instanceuid'] in self.active_uids:
                        if not tag['path'] in self.datasets_to_pass:
                            if new_series:
                                self.datasets_to_pass.append([tag['path']])
                            else:
                                self.datasets_to_pass[-1].append(tag['path'])

                #~ gc.collect()
            #~ gc.collect()
            if flatten_list:
                self.datasets_to_pass = list(itertools.chain.from_iterable(self.datasets_to_pass))
                
            # Generate an instance ID for the module, and write useful information to a temp file
            # that the module can call on
            import datetime
            now = datetime.datetime.now()
            modstamp = name+'_'+version+'_{:02d}{:02d}{:02d}{:02d}{:02d}{:02d}{:06d}'.format(now.year % 1000,
                                        now.month,
                                        now.day,
                                        now.hour,
                                        now.minute,
                                        now.second,
                                        now.microsecond
                          )
            import hashlib
            _hash = hashlib.new('md5')
            _hash.update(bytes(modstamp,'utf-8'))
            instance_id = str(_hash.hexdigest()[0:16]).upper()
            
            # Grab image paths to pass to module
            image_paths = []
            for tag in self.sorted_list:
                if tag['instanceuid'] in self.active_uids:
                    image_paths.append(tag['path'])
            
            
            instance_info = {
                'module_name': self.moduleframe.moduletree.item(selected_module)['text'],
                'module_version': self.moduleframe.moduletree.item(selected_module)['values'][2],
                'module_instance': instance_id,
                'image_directory': self.dicomdir,
                'user_directory': self.userdir,
                'temp_directory': self.tempdir,
                'mippy_version': self.mippy_version,
                'user': self.user,
                'image_paths': image_paths,
                'module_file': active_module.__file__
                }
            # print(instance_info)
            
            active_module.execute(self.master,instance_info,self.datasets_to_pass)
        except:
            raise
            print("Did you select a module?")
            print("Bet you didn't.")
        return
    
    

    def clear_temp_dir(self):
        if os.path.exists(self.tempdir):
            shutil.rmtree(self.tempdir)
            
    def view_header(self):
        if not hasattr(self, 'active_uids'):
            tkinter.messagebox.showerror('ERROR','No image selected.')
            return            
        if len(self.active_uids)>1:
            tkinter.messagebox.showerror('ERROR','You can only view header for a single image/slice at a time.')
            return
        if len(self.active_uids)<1:
            tkinter.messagebox.showerror('ERROR','No image selected.')
            return
        for tag in self.sorted_list:
            if tag['instanceuid'] in self.active_uids:
                dcm_view = Toplevel(self.master)
                dcm_view.text = Text(dcm_view,width=120,height=30)
                ds = pydicom.dcmread(tag['path'])
                if 'SpectroscopyData' in dir(ds):
                    ds.SpectroscopyData=0
                dcm_view.text.insert(END,str(ds))
                dcm_view.text.config(state='disabled')
                dcm_view.text.see('1.0')
                dcm_view.text.pack()
        pass
        
    def compare_headers(self):
        if not hasattr(self, 'active_uids'):
            tkinter.messagebox.showerror('ERROR','No image selected.')
            return
        if len(self.active_uids)<1:
            tkinter.messagebox.showerror('ERROR','No image selected.')
            return
        if not len(self.active_uids)==2:
            tkinter.messagebox.showerror('ERROR','You can only compare headers for 2 single images/slices at a time.')
            return
        dicoms = []
        for tag in self.sorted_list:
            if tag['instanceuid'] in self.active_uids:
                dicoms.append(pydicom.dcmread(tag['path']))
        for ds in dicoms:
            if 'SpectroscopyData' in dir(ds):
                ds.SpectroscopyData = 0
        diffs = compare_dicom(*dicoms)
        dcm_compare = Toplevel(self.master)
        dcm_compare.text = Text(dcm_compare,width=120,height=30)
        dcm_compare.text.tag_config('highlight', foreground='red')
        dcm_compare.text.tag_config('unhighlight', foreground='black')
        if len(diffs)==0:
            dcm_compare.text.insert(END,'No differences found.')
        else:
            dcm_compare.text.insert(END,'DIFFERENCES IN DICOM HEADER (Some tags ignored)\n')
            for row in diffs:
                #~ print row
                dcm_compare.text.insert(END,'\n'+row[0]+':\n')
                dcm_compare.text.insert(END,'1: '+row[1]+'\n','highlight')
                dcm_compare.text.insert(END,'2: '+row[2]+'\n','highlight')
        dcm_compare.text.config(state='disabled')
        dcm_compare.text.pack()
    
    def export_dicom(self):
        
        #~ outdir = os.path.join(self.root_dir,"EXPORT")
        if not hasattr(self, 'active_uids'):
            tkinter.messagebox.showerror('ERROR','No images selected.')
            return
        if len(self.active_uids)<1:
            tkinter.messagebox.showerror('ERROR','No images selected.')
            return
        self.exportdir = tkinter.filedialog.askdirectory(parent=self,initialdir=r"M:",title="Select export directory")
        if self.exportdir is None:
            return
        i=0
        for tag in self.sorted_list:
            if tag['instanceuid'] in self.active_uids:
                fileio.export_dicom_file(load_images_from_uids([tag],self.active_uids,self.tempdir,multiprocess=False)[0][0],self.exportdir)
                i+=1
                self.progress(float(i)/float(len(self.active_uids))*100.)
        self.progress(0.)
        tkinter.messagebox.showinfo('EXPORT FINISHED','Images have finished exporting to:\n'+self.exportdir)
        self.exportdir = None        
        return
    
    def show_log(self):
        logwin = Toplevel()
        logtext = ScrolledText.ScrolledText(logwin)
        with open(self.logpath,'rb') as logfile:
            text = logfile.readlines()
            for row in text:
                logtext.insert(END,row+'\n')
        logtext.pack()
    
    def enable_multiprocessing(self):
        self.multiprocess = True
        tkinter.messagebox.showinfo("INFO","Multiprocessing enabled")
        return
    
    def disable_multiprocessing(self):
        self.multiprocess = False
        tkinter.messagebox.showinfo("INFO","Multiprocessing disabled")
        return

#########################################################

