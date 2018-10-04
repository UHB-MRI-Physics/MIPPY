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
                
                # Set temp directory
                if 'darwin' in sys.platform or 'linux' in sys.platform:
                        self.tempdir = '/tmp/MIPPY_temp_'+self.user                        
                elif 'win' in sys.platform:
                        sys_temp  = os.getenv("TEMP",r'C:\TEMP')
                        self.tempdir = os.path.join(sys_temp,"MIPPY_temp_"+self.user)
                else:
                        tkinter.messagebox.showerror('ERROR', 'Unsupported operating system, please contact the developers.')
                        sys.exit()
                if not os.path.exists(self.tempdir):
                        os.makedirs(self.tempdir)
                
                # Set persistent user directory
                if 'darwin' in sys.platform or 'linux' in sys.platform:
                    #~ self.userdir = os.path.join('/home',self.user,'.mippy')
                    self.userdir = os.path.expanduser('~/.mippy')
                elif 'win' in sys.platform:
                    sys_userdir = os.getenv('APPDATA',os.path.join('C:','Users',self.user))
                    self.userdir = os.path.join(sys_userdir,'.mippy')
                else:
                    tkinter.messagebox.showerror('ERROR', 'Unsupported operating system, please contact the developers.')
                    sys.exit()
                if not os.path.exists(self.userdir):
                    os.makedirs(self.userdir)
                
                # Set default module directory
                if os.path.exists(os.path.join(self.root_dir, 'modules')):
                        self.moduledir = os.path.join(self.root_dir, 'modules')
                        if not self.moduledir in sys.path:
                                sys.path.append(self.moduledir)
                else:
                        self.moduledir = None
                
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

                # Create menu bar for the top of the window
                self.menubar = Menu(master)
                # Create and populate "File" menu
                self.filemenu = Menu(self.menubar, tearoff=0)
                self.filemenu.add_command(label="Load new image directory", command=lambda:self.load_image_directory())
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
                self.helpmenu.add_command(label="Open the wiki",command=lambda:self.load_wiki())
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
                self.moduleframe.moduletree['columns']=('description','author')
                self.moduleframe.moduletree.heading('#0',text='Module Name')
                self.moduleframe.moduletree.heading('description',text='Description')
                self.moduleframe.moduletree.heading('author',text='Author')

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




        def asktoexit(self):
#                if tkMessageBox.askokcancel("Quit?", "Are you sure you want to exit?"):
#                        self.master.destroy()
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
                try:
                    # Unpickle previous directory if available
                    with open(os.path.join(self.userdir,'prevdir.cfg'),'rb') as cfg_file:
                        prevdir = pickle.load(cfg_file)
                    print("PREV DIRECTORY: {}".format(prevdir))
                except:
                    prevdir = r'M:'
                self.dicomdir = tkinter.filedialog.askdirectory(parent=self,initialdir=prevdir,title="Select image directory")
                if not self.dicomdir:
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
                                self.tag_list = self.sorted_list        # Shouldn't need this really...
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
                self.moduledir = tkinter.filedialog.askdirectory(parent=self,initialdir=self.root_dir,title="Select module directory")
                if not self.moduledir:
                        return
                sys.path.append(self.moduledir)
                self.scan_modules_directory()
                return                

        def scan_modules_directory(self):
                self.module_list = []
                viewerconfigpath = resource_filename('mippy.mviewer','config')
                with open(viewerconfigpath,'rb') as file_object:
                        module_info = pickle.load(file_object)
                module_info['dirname']='mippy.mviewer'
                self.module_list.append(module_info)
                
                
                if not (self.moduledir is None or not self.moduledir):
                        for folder in os.listdir(self.moduledir):
                                if not os.path.isdir(os.path.join(self.moduledir,folder)):
                                        continue
                                file_list = os.listdir(os.path.join(self.moduledir,folder))
                                if (('__init__.py' in file_list or '__init__.pyc' in file_list)
                                        and ('module_main.py' in file_list or 'module_main.pyc' in file_list)
                                        and 'config' in file_list):
                                        cfg_file = os.path.join(self.moduledir,folder,'config')
                                        with open(cfg_file,'rb') as file_object:
                                                module_info = pickle.load(file_object)
                                        self.module_list.append(module_info)
                                        #~ print module_info
                        self.module_list = sorted(self.module_list,key=lambda item: item['name'])
                
                try:
                        for item in self.moduleframe.moduletree.get_children():
                                self.moduleframe.moduletree.delete(item)
                        print("Existing module tree cleared")
                except Exception:
                        print("New module tree created")
                        pass
                for module in self.module_list:
                        self.moduleframe.moduletree.insert('','end',module['dirname'],
                                text=module['name'],values=(module['description'],module['author']))

                #~ self.master.progress = 50.
                return

        def exit_program(self):
                self.asktoexit()
                return

        def load_wiki(self):
                print("Load wiki")
                webbrowser.open_new('http://tree.taiga.io/project/robflintham-mippy/wiki/home')
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
##                verpath = resource_filename('mippy','resources/version.info')
##                with open(verpath,'rb') as infofile:
##                        info = infofile.read()
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
                # Run a garbage collect to clear anything left over from previous module loading
                gc.collect()
                try:
                        
                        moduledir = self.moduleframe.moduletree.selection()[0]
                        module_name = moduledir+'.module_main'
                        if not module_name in sys.modules:
                                active_module = importlib.import_module(module_name)
                        else:
                                active_module = importlib.import_module(module_name)
                                imp.reload(active_module)
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
                                
                                #~ self.datasets_to_pass = []
                                #~ dcm_info = []
                                #~ previous_tag = None
                                #~ if not self.multiprocess or ('win' in sys.platform and len(self.active_uids)<25):
                                        #~ for tag in self.sorted_list:
                                                #~ if tag['instanceuid'] in self.active_uids:
                                                        #~ # Check to see if new series
                                                        #~ if previous_tag:
                                                                #~ if tag['seriesuid']==previous_tag['seriesuid']:
                                                                        #~ new_series = False
                                                                #~ else:
                                                                        #~ new_series = True
                                                        #~ else:
                                                                #~ new_series = True
                                                        #~ # First, check if dataset is already in temp files
                                                        #~ temppath = os.path.join(self.tempdir,tag['instanceuid']+'.mds')
                                                        #~ if os.path.exists(temppath):
                                                                #~ print "TEMP FILE FOUND",tag['instanceuid']
                                                                #~ with open(temppath,'rb') as tempfile:
                                                                        #~ if new_series:
                                                                                #~ self.datasets_to_pass.append([pickle.load(tempfile)])
                                                                        #~ else:
                                                                                #~ self.datasets_to_pass[-1].append(pickle.load(tempfile))
                                                                        #~ tempfile.close()
                                                        #~ else:
                                                                #~ if not tag['path']==self.open_file:
                                                                        #~ self.open_ds = pydicom.dcmread(tag['path'])
                                                                        #~ self.open_file = tag['path']
                                                                #~ if not tag['enhanced']:
                                                                        #~ if new_series:
                                                                                #~ self.datasets_to_pass.append([self.open_ds])
                                                                        #~ else:
                                                                                #~ self.datasets_to_pass[-1].append(self.open_ds)
                                                                #~ else:
                                                                        #~ split_ds = get_frame_ds(tag['instance'],self.open_ds)
                                                                        #~ if new_series:
                                                                                #~ self.datasets_to_pass.append([split_ds])
                                                                        #~ else:
                                                                                #~ self.datasets_to_pass[-1].append(split_ds)
                                                                        #~ save_temp_ds(split_ds,self.tempdir,tag['instanceuid']+'.mds')
                                                        #~ previous_tag = tag
                                #~ else:
                                        #~ for tag in self.sorted_list:
                                                #~ if tag['instanceuid'] in self.active_uids:
                                                        #~ dcm_info.append((tag['instanceuid'],tag['path'],tag['instance']))
                                        #~ f = partial(get_dataset,tempdir=self.tempdir)
                                        #~ self.datasets_to_pass = multithread(f,dcm_info,progressbar=self.progress)
                                        #~ # Group by series, to be flattened later if 1D list required
                                        #~ self.datasets_to_pass = [list(g) for k,g, in itertools.groupby(self.datasets_to_pass, lambda ds: ds.SeriesInstanceUID)]
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
                        active_module.execute(self.master,self.dicomdir,self.datasets_to_pass)
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


                        

# This launches the application

#~ if __name__=='mippy.application':
        #~ freeze_support()
        #~ print "Launching MIPPY..."
        #~ # Set up logging
        #~ try:
                #~ if sys.argv [1]=='debug':
                        #~ debug_mode=True
                #~ else:
                        #~ debug_mode=False
        #~ except:
                #~ debug_mode=False
        #~ if not debug_mode:
                #~ logpath = os.path.join(os.getcwd(),"MIPPY-logs",str(datetime.now()).replace(":",".").replace(" ","_")+".txt")
                #~ try:
                        #~ os.makedirs(os.path.split(logpath)[0])
                #~ except:
                        #~ pass
                #~ with open(logpath,'wb') as logout:
                        #~ logout.write('LOG FILE\n')
                #~ redir_out = RedirectText(logpath)
                #~ redir_err = RedirectText(logpath)
                #~ sys.stdout = redir_out
                #~ sys.stderr = redir_err
                
        #~ # Start application behind splash screen
        #~ try:
                #~ from . import splash
                #~ splashpath =  resource_filename('mippy','resources/splash.jpg')
                #~ root_window = Tk()
                #~ root_window.title("MIPPY: Modular Image Processing in Python")
                #~ root_window.minsize(650,400)
                #~ root_path = os.getcwd()
                #~ if "nt" == os.name:
                        #~ impath = resource_filename('mippy','resources/brain_orange.ico')
                #~ else:
                        #~ impath = '@'+resource_filename('mippy','resources/brain_bw.xbm')
                #~ root_window.wm_iconbitmap(impath)

                #~ with splash.SplashScreen(root_window,splashpath, 0.5):
                        #~ root_app = MIPPYMain(master = root_window)
                #~ root_app.mainloop()
        #~ except Exception as e:
                #~ print e
                #~ tkMessageBox.showerror('ERROR','Error occurred. Please consult log files.')

