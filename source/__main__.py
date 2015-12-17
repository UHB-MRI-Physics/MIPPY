print "Importing packages..."
print "    DICOM"
import dicom
print "    Tkinter (GUI)"
import tkMessageBox
import tkFileDialog
from Tkinter import *
from ttk import *
print "    os"
import os
print "    NumPy"
import numpy as np
print "    Python Imaging Library (PIL)"
from PIL import Image, ImageTk
#~ print "    math"
#~ from math import floor
#~ print "    easyGUI"
#~ from easygui import diropenbox, codebox
print "    date/time"
import datetime
import time
#~ print "    SciPy"
#~ from scipy.signal import convolve2d
#~ from scipy.ndimage.measurements import center_of_mass
#~ from scipy.ndimage.filters import convolve
#~ from scipy.ndimage import map_coordinates
#~ from scipy.optimize import curve_fit
import importlib
import sys
from functions.file_functions import list_all_files

print "Initialising GUI...\n"

class ToolboxHome(Frame):
	
	## Define any global attributes/variables you'll need here.  Use as few of these
	## as possible as they will exist in RAM for as long as the program is running
	## and are a waste of memory if they're not needed.  They also create massive
	## confusion if you want to use similar/the same variable names in other modules.
	
	
	
	
	
	
	
	
	def __init__(self, master):
		"""
		This is the function which is called automatically when you create an object of
		this class, to initiate ("init", get it?) the object.
		
		This is where the GUI is first created and populated with buttons, image canvasses,
		tabs, whatever.  This function can also call other functions should you wish to split
		the code down further.
		"""
		
		# Initialises the GUI as a "Frame" object and gives it the name "master"
		Frame.__init__(self, master)
		self.master = master
		
		# Catches any calls to close the window (e.g. clicking the X button in Windows) and pops
		# up an "Are you sure?" dialog
		self.master.protocol("WM_DELETE_WINDOW", self.asktoexit)
		
		# Create menu bar for the top of the window
		self.master.menubar = Menu(master)
		# Create and populate "File" menu
		self.master.filemenu = Menu(self.master.menubar, tearoff=0)
		self.master.filemenu.add_command(label="Load image directory", command=lambda:self.load_image_directory())
		self.master.filemenu.add_command(label="Refresh current directory", command=lambda:self.refresh_directory())
		self.master.filemenu.add_command(label="Exit program",command=lambda:self.exit_program())
		# Create and populate "Help" menu
		self.master.helpmenu = Menu(self.master.menubar, tearoff=0)
		self.master.helpmenu.add_command(label="Open the wiki",command=lambda:self.load_wiki())
		self.master.helpmenu.add_command(label="About...",command=lambda:self.display_version_info())
		# Add menus to menubar and display menubar in window
		self.master.menubar.add_cascade(label="File",menu=self.master.filemenu)
		self.master.menubar.add_cascade(label="Help",menu=self.master.helpmenu)
		self.master.config(menu=self.master.menubar)
		
		# Create frames to hold DICOM directory tree and module list
		self.master.dirframe = Frame(self.master,height=100)
		self.master.moduleframe = Frame(self.master)
		self.master.dirframe = Frame(self.master)
		self.master.moduleframe = Frame(self.master)
		
		# Create canvas object to draw images in
		self.master.imcanvas = Canvas(self.master,bd=0,width=256, height=256)
		self.master.imcanvas.create_rectangle((0,0,256,256),fill='black')
		
		# Create buttons:
		# "Start module"
		self.master.loadmodulebutton = Button(self.master,text="Load module",command=lambda:self.load_selected_module())
		
		# Use "grid" to position objects within "master"
		self.master.dirframe.grid(row=0,column=0,columnspan=2,rowspan=1,sticky='nsew')
		self.master.imcanvas.grid(row=1,column=0,sticky='nsew')
		self.master.moduleframe.grid(row=1,column=1,sticky='nsew')
		self.master.loadmodulebutton.grid(row=2,column=1,sticky='nsew')
		
		# Set row and column weights to handle resizing
		self.master.rowconfigure(0,weight=10)
		self.master.rowconfigure(1,weight=1)
		self.master.rowconfigure(2,weight=1)
		self.master.columnconfigure(0,weight=1)
		self.master.columnconfigure(1,weight=10)
		
		
		#~ self.master.test_button_1 = Button(master, text="Test button 1",command=lambda:self.load_test_module())
		#~ self.master.test_button_2 = Button(master, text="Test button 2")
		
		#~ self.master.test_button_1.grid(row=0,column=0,sticky='nsew')
		#~ self.master.test_button_2.grid(row=0,column=1,sticky='nsew')
		
		#~ self.master.rowconfigure(0,weight=1)
		#~ self.master.columnconfigure(0,weight=1)
		#~ self.master.columnconfigure(1,weight=1)
		
		master.focus()
		
			
	def asktoexit(self):
		if tkMessageBox.askokcancel("Quit?", "Are you sure you want to exit?"):
			#self.master.destroy()
			sys.exit()
		return
		
	def load_image_directory(self):
		print "Load image directory"
		dicomdir = tkFileDialog.askdirectory(parent=self.master,initialdir=r"M:",title="Select image directory")
		if not dicomdir:
			return
		ask_recursive = tkMessageBox.askyesno("Search recursively?","Do you want to include all subdirectories?")
		print dicomdir
		print ask_recursive
		path_list = []
		path_list = list_all_files(dicomdir,recursive=ask_recursive)
		self.build_dicom_tree(path_list)
		
		return
		
	def build_dicom_tree(self,path_list):
		# Build tree by first organising list - inspecting study UID, series UID, instance number
		#~ currentframeheight=self.master.dirframe.config()['height']
		#~ currentframewidth=self.master.dirframe.config()['width']
		
		tag_list = []
		
		for p in path_list:
			ds = None
			try:
				ds = dicom.read_file(p)				
			except:
				print p+'\n...is not a valid DICOM file and is being ignored.'
				continue
			if ds:
				#~ print os.path.split(p)[1]
				
				try:
					# There has to be a better way of testing this...? If "ImageType" tag doesn't exist...
					type = ds.ImageType
				except:
					continue
					
				seriesdesc = ds.SeriesDescription
				if "PHOENIXZIPREPORT" in seriesdesc.upper():
					continue
				mode = "Assumed MR Image Storage"
				try:
					mode = str(ds.SOPClassUID)
				except:
					pass
				if "SOFTCOPY" in mode.upper() or "BASIC TEXT" in mode.upper():
					continue
				if mode.upper()=="ENHANCED MR IMAGE STORAGE":
					enhanced = True
					frames = ds.NumberOfFrames
				else:
					enhanced = False
					frames = 1
				study_uid = ds.StudyInstanceUID
				series_uid = ds.SeriesInstanceUID
				instance_uid = ds.SOPInstanceUID
				name = ds.PatientName
				date = ds.StudyDate
				series = ds.SeriesNumber
				time = ds.StudyTime
				studydesc = ds.StudyDescription
				if enhanced:
					instance = np.array(range(frames))+1
				else:
					instance = [ds.InstanceNumber]
				for i in instance:
					tag_list.append(dict([('date',date),('time',time),('name',name),('studyuid',study_uid),
									('series',series),('seriesuid',series_uid),('studydesc',studydesc),
									('seriesdesc',seriesdesc),('instance',i),('instanceuid',instance_uid),
									('path',p),('enhanced',enhanced)]))
		
		# This should sort the list in to your initial order for the tree
		sorted_list = sorted(tag_list)
		
		# This is to finish tomorrow.  Add to tree based on study UID, then instance number/UID.
		# Use the UID as the ID of the list item???  Then there's at least some logic to it!
		# Need to remember to split correct tag info for enhanced files.  Maybe build a function for that
		# into the file_functions methods rather than here?  Easier to call then, especially in other modules.
		#~ for scan in sorted_list:
			#~ if not scan['enhanced']:
		
		i=0
		try:
			self.master.dirframe.dicomtree.destroy()
		except:
			pass
		self.master.dirframe.dicomtree = Treeview(self.master.dirframe)
		self.master.dirframe.dicomtree['columns']=('date','name','desc')
		self.master.dirframe.dicomtree.heading('date',text='Study Date')
		self.master.dirframe.dicomtree.heading('name',text='Patient Name')
		self.master.dirframe.dicomtree.heading('desc',text='Description')
		for scan in sorted_list:
			if not self.master.dirframe.dicomtree.exists(scan['studyuid']):
				i+=1
				self.master.dirframe.dicomtree.insert('','end',scan['studyuid'],text=str(i).zfill(4),
												values=(scan['date'],scan['name'],scan['studydesc']))
			if not self.master.dirframe.dicomtree.exists(scan['seriesuid']):
				self.master.dirframe.dicomtree.insert(scan['studyuid'],'end',scan['seriesuid'],
											text='Series '+str(scan['series']).zfill(3),
											values=('','',scan['seriesdesc']))
			self.master.dirframe.dicomtree.insert(scan['seriesuid'],'end',scan['instanceuid'],
											text='Image '+str(scan['instance']).zfill(3),
											values=('','',''))
		
		
		self.master.dirframe.dicomtree.scrollbarx = Scrollbar(self.master.dirframe.dicomtree,orient='horizontal')
		self.master.dirframe.dicomtree.scrollbarx.pack(side='bottom',fill='x')
		self.master.dirframe.dicomtree.scrollbarx.config(command=self.master.dirframe.dicomtree.xview)
		self.master.dirframe.dicomtree.scrollbary = Scrollbar(self.master.dirframe.dicomtree)
		self.master.dirframe.dicomtree.scrollbary.pack(side='right',fill='y')
		self.master.dirframe.dicomtree.scrollbary.config(command=self.master.dirframe.dicomtree.yview)
		
		
		
		self.master.dirframe.dicomtree.grid(row=0,column=0,sticky='nsew')
		self.master.dirframe.rowconfigure(0,weight=1)
		self.master.dirframe.columnconfigure(0,weight=1)
		
		#~ self.master.dirframe.config(width=currentframewidth,height=currentframeheight)
		
		#~ self.master.dirframe.dicomtree.pack(expand=True)
		
		
		
		
		
		return
		
		
	def refresh_directory(self):
		print "Refresh directory"
		return
		
	def exit_program(self):
		self.asktoexit()
		return
		
	def load_wiki(self):
		print "Load wiki"
		return
		
	def display_version_info(self):
		print "Display version info"
		return
			
	def load_test_module(self):
		current_module = this_module = importlib.import_module("analysis_modules.test_module_1.module_main")
		current_module.load_module()
		return
		
	def load_selected_module(self):
		pass
		
		

#########################################################
"""
Here is where the program is actually executed.  "root_window" Tk() object is created (Tk is 
the GUI package), then given a title and dimensions as attributes, then used to create the
"ToolboxHome" application.  The "mainloop" function then enters the actual application.
"""

root_window = Tk()
root_window.title("MIPPY: Modular Image Processing in Python")
root_window.minsize(650,400)
#root_window.geometry("+50+50")
#root_window.wm_resizeable(False,False)
root_app = ToolboxHome(master = root_window)
root_app.mainloop()