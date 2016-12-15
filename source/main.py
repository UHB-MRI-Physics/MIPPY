"""
Icon attribution:
Icon made by Freepik from www.flaticon.com
"""

print "Importing packages..."
print "    Pickle/cPickle"
import cPickle as pickle
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
print "    date/time"
from datetime import datetime
import time
print "    importlib"
import importlib
print "    web broswer interface"
import webbrowser
print "    sys"
import sys
print "    high-level file operations (shutil)"
import shutil
print "    MIPPY file functions"
from functions.file_functions import *
print "    MIPPY viewer functions"
from functions.viewer_functions import *
print "    MIPPY DICOM functions"
from functions.dicom_functions import *
print "    Garbage Collection"
import gc

print "Initialising GUI...\n"

#os.system('xset r off')


class ToolboxHome(Frame):

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

		self.root_dir = os.getcwd()

		# Initialises the GUI as a "Frame" object and gives it the name "master"
		Frame.__init__(self, master)
		self.master = master

		# Catches any calls to close the window (e.g. clicking the X button in Windows) and pops
		# up an "Are you sure?" dialog
		self.master.protocol("WM_DELETE_WINDOW", self.asktoexit)



		#~ # Set up logfile in logs directory
		#~ logpath=os.path.join(os.getcwd(),"logs",str(datetime.now()).replace(":",".").replace(" ","_")+".txt")
		#~ with open(logpath,'w') as logout:
			#~ logout.write('LOG FILE\n')


		#~ # Add capture for stdout and stderr output for log file, and scrollable text box
		#~ self.master.logoutput = ScrolledText.ScrolledText(self.master,height=6)
		#~ redir_out = RedirectText(self.master.logoutput,logpath)
		#~ redir_err = RedirectText(self.master.logoutput,logpath)
		#~ sys.stdout = redir_out
		#~ sys.stderr = redir_err

		'''
		This section is to determine the host OS, and set up the appropriate temp
		directory for images.
		Windows = C:\Temp
		Mac = /tmp
		Linux = /tmp
		'''
		if 'darwin' in sys.platform or 'linux' in sys.platform:
			self.tempdir = '/tmp/MIPPY_temp'
		elif 'win' in sys.platform:
			self.tempdir = r'C:\Temp\MIPPY_temp'
		else:
			tkMessageBox.showerror('ERROR', 'Unsupported operating system, please contact the developers.')
			sys.exit()
#		print self.tempdir

		# Create menu bar for the top of the window
		self.menubar = Menu(master)
		# Create and populate "File" menu
		self.filemenu = Menu(self.menubar, tearoff=0)
		self.filemenu.add_command(label="Load image directory", command=lambda:self.load_image_directory())
		self.filemenu.add_command(label="Refresh module list", command=lambda:self.scan_modules_directory())
		self.filemenu.add_command(label="Exit program",command=lambda:self.exit_program())
		# Create and populate "Help" menu
		self.helpmenu = Menu(self.menubar, tearoff=0)
		self.helpmenu.add_command(label="Open the wiki",command=lambda:self.load_wiki())
		self.helpmenu.add_command(label="About...",command=lambda:self.display_version_info())
		# Add menus to menubar and display menubar in window
		self.menubar.add_cascade(label="File",menu=self.filemenu)
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

		# Bind "module select" event to required action
		self.moduleframe.moduletree.bind('<<TreeviewSelect>>',self.module_window_click)

		# Just adding a random line to the tree for testing
		#self.master.moduleframe.moduletree.insert('','end',"test row",text="Blah blah",values=("Option 1","Option 2"))

		# Create canvas object to draw images in
		self.imcanvas = MIPPYCanvas(self.master,bd=0,width=256, height=256,drawing_enabled=False)


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
#		if tkMessageBox.askokcancel("Quit?", "Are you sure you want to exit?"):
#			self.master.destroy()
			#~ sys.exit()
		mbox = tkMessageBox.Message(
			title='Delete temporary files?',
			message='Would you like to delete all MIPPY temp files?',
			icon=tkMessageBox.QUESTION,
			type=tkMessageBox.YESNOCANCEL,
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
		print "You clicked on the module window."

	def load_image_directory(self):
		print "Load image directory"
		self.dicomdir = tkFileDialog.askdirectory(parent=self,initialdir=r"M:",title="Select image directory")
		if not self.dicomdir:
			return
		ask_recursive = tkMessageBox.askyesno("Search recursively?","Do you want to include all subdirectories?")

		self.path_list = []
		self.active_series = None

		self.path_list = list_all_files(self.dicomdir,file_list=self.path_list,recursive=ask_recursive)

		self.filter_dicom_files()
		self.build_dicom_tree()

		return

	def filter_dicom_files(self):
		self.tag_list = []
		for p in self.path_list:
			self.progress(100*(float(self.path_list.index(p))/float(len(self.path_list))))
			tags = collect_dicomdir_info(p,tempdir=self.tempdir)
			if tags:
				for row in tags:
					self.tag_list.append(row)
		self.progress(0.)
		return

	def build_dicom_tree(self):
		print "function_started"
		# This should sort the list into your initial order for the tree - maybe implement a more customised sort if necessary?
		from operator import itemgetter
		self.sorted_list = sorted(self.tag_list, key=itemgetter('name','date','time','studyuid','series','seriesuid','instance','instanceuid'))

		#~ i=0
		print self.dirframe.dicomtree.get_children()
		try:
			for item in self.dirframe.dicomtree.get_children():
				self.dirframe.dicomtree.delete(item)
			print "Existing tree cleared"
		except Exception:
			print "New tree created"
			pass
		repeats_found = False
		n_repeats = 0
		for scan in self.sorted_list:
			print "Adding to tree: "+scan['path']
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
			tkMessageBox.showwarning("WARNING",str(n_repeats)+" repeat image UID's found and ignored.")
		self.dirframe.dicomtree.update()
		#~ self.master.progress = 100
		return

	def scan_modules_directory(self):
		self.module_list = []
		for folder in os.listdir(os.path.join(self.root_dir,'modules')):
			if not os.path.isdir(os.path.join(self.root_dir,'modules',folder)):
				continue
			file_list = os.listdir(os.path.join(self.root_dir,'modules',folder))
			if (('__init__.py' in file_list or '__init__.pyc' in file_list)
				and ('module_main.py' in file_list or 'module_main.pyc' in file_list)
				and 'config' in file_list):
				cfg_file = os.path.join(self.root_dir,'modules',folder,'config')
				with open(cfg_file,'r') as file_object:
					module_info = pickle.load(file_object)
				self.module_list.append(module_info)
		self.module_list = sorted(self.module_list)
		try:
			for item in self.moduleframe.moduletree.get_children():
				self.moduleframe.moduletree.delete(item)
			print "Existing module tree cleared"
		except Exception:
			print "New module tree created"
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
		print "Load wiki"
		webbrowser.open_new('http://tree.taiga.io/project/robflintham-mippy/wiki/home')
		return

	def display_version_info(self):
		print "Display version info"
		info = ""
		with open('source/version.info','r') as infofile:
			info = infofile.read()
		tkMessageBox.showinfo("MIPPY: Version info",info)
		return

	def load_selected_module(self):
#		print "DO NOTHING!"
		gc.collect()
		try:
			moduledir = self.moduleframe.moduletree.selection()[0]
			module_name = 'modules.'+moduledir+'.module_main'
			if not module_name in sys.modules:
				active_module = importlib.import_module(module_name)
			else:
				active_module = importlib.import_module(module_name)
				reload(active_module)
			preload_dicom = active_module.preload_dicom()
			#~ if preload_dicom=='full':
			if preload_dicom:
				self.datasets_to_pass = []
				for tag in self.sorted_list:

					if tag['instanceuid'] in self.active_uids:
						# First, check if dataset is already in temp files
						temppath = os.path.join(self.tempdir,tag['instanceuid']+'.mds')
						if os.path.exists(temppath):
							print "TEMP FILE FOUND",tag['instanceuid']
							with open(temppath,'rb') as tempfile:
								self.datasets_to_pass.append(pickle.load(tempfile))
								tempfile.close()
							continue
						else:
							if not tag['path']==self.open_file:
								self.open_ds = dicom.read_file(tag['path'])
								self.open_file = tag['path']
								gc.collect()
							if not tag['enhanced']:
	#							print tag['path']
	#							print type(tag['path'])
								self.datasets_to_pass.append(self.open_ds)
							else:
	#							ds = dicom.read_file(tag['path'])
	#							print tag['path']
	#							print type(tag['path'])
								# Check if image already exists in temp files
								split_ds = get_frame_ds(self.open_ds,tag['instance'])
								self.datasets_to_pass.append(split_ds)
								save_temp_ds(split_ds,self.tempdir,tag['instanceuid']+'.mds')
			#~ elif preload_dicom=='minimal':
				#~ self.datasets_to_pass = []
				#~ for tag in self.sorted_list:
					#~ if tag['instanceuid'] in self.active_uids:
						#~ self.datasets_to_pass.append(tag)
			else:
				self.datasets_to_pass = []
				for uid in self.active_uids:
					for tag in self.sorted_list:
						if tag['instanceuid'] in self.active_uids:
							if not tag['path'] in self.datasets_to_pass:
								self.datasets_to_pass.append(tag['path'])
			gc.collect()
			active_module.execute(self.master,self.dicomdir,self.datasets_to_pass)
		except:
			raise
			print "Did you select a module?"
			print "Bet you didn't."
		return

	def clear_temp_dir(self):
		if os.path.exists(self.tempdir):
			shutil.rmtree(self.tempdir)

#########################################################
"""
Here is where the program is actually executed.  "root_window" Tk() object is created (Tk is
the GUI package), then given a title and dimensions as attributes, then used to create the
"ToolboxHome" application.  The "mainloop" function then enters the actual application.
"""


