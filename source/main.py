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
#~ print "    math"
#~ from math import ceil
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
print "    MIPPY file functions"
from functions.file_functions import *
print "    MIPPY viewer functions"
from functions.viewer_functions import *
print "    MIPPY DICOM functions"
from functions.dicom_functions import *

print "    threading"
import threading
print "    queue"
import Queue as queue

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
		
		# Create menu bar for the top of the window
		self.master.menubar = Menu(master)
		# Create and populate "File" menu
		self.master.filemenu = Menu(self.master.menubar, tearoff=0)
		self.master.filemenu.add_command(label="Load image directory", command=lambda:self.load_image_directory())
		self.master.filemenu.add_command(label="Refresh module list", command=lambda:self.scan_modules_directory())
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
		self.master.dirframe = Frame(self.master)
		self.master.moduleframe = Frame(self.master)
		self.master.dirframe = Frame(self.master)
		self.master.moduleframe = Frame(self.master)
		
		# Create DICOM treeview
		self.master.dirframe.dicomtree = Treeview(self.master.dirframe)
		
		# Set names and widths of columns in treeviews
		self.master.dirframe.dicomtree['columns']=('date','name','desc')
		self.master.dirframe.dicomtree.heading('date',text='Study Date')
		self.master.dirframe.dicomtree.heading('name',text='Patient Name')
		self.master.dirframe.dicomtree.heading('desc',text='Description')
		self.master.dirframe.dicomtree.column('#0',width=100,stretch=False)
		self.master.dirframe.dicomtree.column('date',width=100,stretch=False)
		self.master.dirframe.dicomtree.column('name',width=200)
		self.master.dirframe.dicomtree.column('desc',width=500)
		
		# Create scrollbars
		self.master.dirframe.scrollbarx = Scrollbar(self.master.dirframe,orient='horizontal')
		self.master.dirframe.scrollbarx.config(command=self.master.dirframe.dicomtree.xview)
		self.master.dirframe.scrollbary = Scrollbar(self.master.dirframe)
		self.master.dirframe.scrollbary.config(command=self.master.dirframe.dicomtree.yview)
		self.master.dirframe.dicomtree.configure(yscroll=self.master.dirframe.scrollbary.set, xscroll=self.master.dirframe.scrollbarx.set)
		
		# Use "grid" to postion treeview and scrollbars in DICOM frame and assign weights to columns and rows
		self.master.dirframe.dicomtree.grid(row=0,column=0,sticky='nsew')
		self.master.dirframe.scrollbarx.grid(row=1,column=0,sticky='nsew')
		self.master.dirframe.scrollbary.grid(row=0,column=1,sticky='nsew')
		
		# Set "weights" (relatve amount of stretchability when resizing window) for each row and column
		self.master.dirframe.rowconfigure(0,weight=1)
		self.master.dirframe.columnconfigure(0,weight=1)
		self.master.dirframe.rowconfigure(1,weight=0)
		self.master.dirframe.columnconfigure(1,weight=0)
		
		# Bind "change selection" event to method to update the image display
		self.master.dirframe.dicomtree.bind('<<TreeviewSelect>>',self.dir_window_selection)
		
		# Remove focus from dicomtree widget when mouse not hovering
		#~ self.master.dirframe.dicomtree.bind('<Leave>',self.dicomtree_nofocus)
		#~ self.master.dirframe.dicomtree.bind('<Enter>',self.dicomtree_focus)	
		
		
		# Create module treeview
		self.master.moduleframe.moduletree = Treeview(self.master.moduleframe)
		
		# Set names and widths of columns in treeview
		self.master.moduleframe.moduletree['columns']=('description','author')
		self.master.moduleframe.moduletree.heading('#0',text='Module Name')
		self.master.moduleframe.moduletree.heading('description',text='Description')
		self.master.moduleframe.moduletree.heading('author',text='Author')
		
		# Create scrollbars
		self.master.moduleframe.scrollbarx = Scrollbar(self.master.moduleframe,orient='horizontal')
		self.master.moduleframe.scrollbarx.config(command=self.master.moduleframe.moduletree.xview)
		self.master.moduleframe.scrollbary = Scrollbar(self.master.moduleframe)
		self.master.moduleframe.scrollbary.config(command=self.master.moduleframe.moduletree.yview)
		self.master.moduleframe.moduletree.configure(yscroll=self.master.moduleframe.scrollbary.set, xscroll=self.master.moduleframe.scrollbarx.set)
		
		# Use "grid" to postion treeview and scrollbars in DICOM frame and assign weights to columns and rows
		self.master.moduleframe.moduletree.grid(row=0,column=0,sticky='nsew')
		self.master.moduleframe.scrollbarx.grid(row=1,column=0,sticky='nsew')
		self.master.moduleframe.scrollbary.grid(row=0,column=1,sticky='nsew')
		
		# Set "weights" (relatve amount of stretchability when resizing window) for each row and column
		self.master.moduleframe.rowconfigure(0,weight=1)
		self.master.moduleframe.columnconfigure(0,weight=1)
		self.master.moduleframe.rowconfigure(1,weight=0)
		self.master.moduleframe.columnconfigure(1,weight=0)
		
		# Remove focus from moduletree widget when mouse not hovering
		#~ self.master.moduleframe.moduletree.bind('<Leave>',self.moduletree_nofocus)
		#~ self.master.moduleframe.moduletree.bind('<Enter>',self.moduletree_focus)
		
		# Load modules to list
		self.scan_modules_directory()
		
		# Bind "module select" event to required action
		self.master.moduleframe.moduletree.bind('<<TreeviewSelect>>',self.module_window_click)
		
		# Just adding a random line to the tree for testing
		#self.master.moduleframe.moduletree.insert('','end',"test row",text="Blah blah",values=("Option 1","Option 2"))
				
		# Create canvas object to draw images in
		self.master.imcanvas = Canvas(self.master,bd=0,width=256, height=256)
		self.reset_small_canvas()
		
		# Bind methods for window and level to canvas (right mouse click)
		self.master.imcanvas.bind('<Button-3>',self.canvas_right_click)
		self.master.imcanvas.bind('<B3-Motion>',self.canvas_right_drag)
		self.master.imcanvas.bind('<Double-Button-3>',self.canvas_right_doubleclick)
		self.master.imcanvas.bind('<ButtonRelease-3>',self.canvas_right_click_release)
		# for Windows
		#~ self.master.bind('<MouseWheel>',self.slice_scroll_wheel)
		#~ # for Linux
		#~ self.master.imcanvas.bind('<Button-4>',self.slice_scroll_wheel)
		#~ self.master.imcanvas.bind('<Button-5>',self.slice_scroll_wheel)
		#~ self.master.imcanvas.bind('<Enter>',self.imcanvas_focus)
		#~ self.master.imcanvas.bind('<Leave>',self.imcanvas_nofocus)
		#~ self.master.imcanvas.active = False
		
		
		# Create button to control image scrolling
		self.master.scrollbutton = Button(self.master, text="SLICE + / -")
		self.master.scrollbutton.bind('<Button-1>',self.slice_scroll_button_click)
		self.master.scrollbutton.bind('<B1-Motion>',self.slice_scroll_button_drag)
		
		# Create buttons:
		# "Load module"
		self.master.loadmodulebutton = Button(self.master,text="Load module",command=lambda:self.load_selected_module())
		
		# Add progressbar
		self.master.progressbar = Progressbar(self.master, mode='determinate')
		# Assign variable to progressbar
		#~ self.master.progress = 0
		#~ self.master.progresstarget = 0
		#~ self.master.progressbar['variable'] = self.master.progress
		# Create queue for threaded functions???
		#~ self.master.queue = queue.Queue()
		
		# Use "grid" to position objects within "master"
		self.master.dirframe.grid(row=0,column=0,columnspan=2,rowspan=1,sticky='nsew')
		self.master.imcanvas.grid(row=1,column=0,sticky='nsew')
		self.master.moduleframe.grid(row=1,column=1,sticky='nsew')
		self.master.loadmodulebutton.grid(row=2,column=1,sticky='nsew')
		self.master.scrollbutton.grid(row=2,column=0,sticky='nsew')
		#~ self.master.logoutput.grid(row=3,column=0,rowspan=1,columnspan=2,sticky='nsew')
		self.master.progressbar.grid(row=3,column=0,rowspan=1,columnspan=2,sticky='nsew')
		
		# Set row and column weights to handle resizing
		self.master.rowconfigure(0,weight=1)
		self.master.rowconfigure(1,weight=0)
		self.master.rowconfigure(2,weight=0)
		#~ self.master.rowconfigure(3,weight=0)
		self.master.columnconfigure(0,weight=0)
		self.master.columnconfigure(1,weight=1)
		
		master.focus()
		
	#~ def dicomtree_focus(self,event):
		#~ self.master.dirframe.focus()
		#~ return
		
	#~ def dicomtree_nofocus(self,event):
		#~ self.master.focus()
		#~ return
		
	#~ def moduletree_focus(self,event):
		#~ self.master.moduleframe.focus()
		#~ return
		
	#~ def moduletree_nofocus(self,event):
		#~ self.master.focus()
		#~ return
	
	#~ def imcanvas_focus(self,event):
		#~ self.master.imcanvas.active = True
		#~ print "grab"
		#~ self.master.imcanvas.grab_current()
		self.master.imcanvas.focus()
		#~ return
		
	#~ def imcanvas_nofocus(self,event):
		#~ self.master.imcanvas.active = False
		#~ print "grab release"
		#~ self.master.imcanvas.grab_release()
		self.master.focus()
		#~ return
	
	def reset_small_canvas(self):
		self.master.imcanvas.delete('all')
		self.master.imcanvas.create_rectangle((0,0,256,256),fill='black')
		self.master.preview_slices = []
		self.master.active_slice = None
		return
		
	def slice_scroll_button_click(self,event):
		self.master.click_x = event.x
		self.master.click_y = event.y
		#~ print "CLICK"
		return
		
	def slice_scroll_button_drag(self,event):
		#~ print "MOVE"
		if self.master.preview_slices==[]:
			# If no active display slices, just skip this whole function
			return
		xmove = event.x-self.master.click_x
		ymove = event.y-self.master.click_y
		#~ print xmove
		#~ print ymove
		
		# Want to move 1 slice every time the mouse is moved a number of pixels up or down
		# Higher sensitivity number = less sensitive!
		sensitivity=5
		if abs(ymove)>sensitivity:
			if ymove<0 and not self.master.active_slice+1==len(self.master.preview_slices):
				self.master.active_slice+=1
				self.refresh_preview_image()
			elif ymove>0 and not self.master.active_slice==0:
				self.master.active_slice-=1
				self.refresh_preview_image()
			self.master.click_x = event.x
			self.master.click_y = event.y
		return
		
	#~ def slice_scroll_wheel(self,event):
		#~ if not self.master.imcanvas.active or self.master.preview_slices == []:
			#~ return
		if self.master.preview_slices == []:
			return
		#~ print "scroll!"
		#~ print event
		#~ if (event.num==5 or event.delta==-120) and not self.master.active_slice==0:
			#~ self.master.active_slice-=1
			#~ self.refresh_preview_image()
		#~ elif (event.num==4 or event.delta==120) and not self.master.active_slice+1==len(self.master.preview_slices):
			#~ self.master.active_slice+=1
			#~ self.refresh_preview_image()
		#~ return
		
	def canvas_right_doubleclick(self,event):
		if self.master.preview_slices == []:
			return
		
		self.master.temp_window = self.master.default_window
		self.master.temp_level = self.master.default_level
		self.master.window = self.master.default_window
		self.master.level = self.master.default_level
		
		for image in self.master.preview_slices:
			image.wl_and_display(window = self.master.default_window, level = self.master.default_level)
		
		self.refresh_preview_image()
		
		return
		
	def canvas_right_click(self,event):
		if self.master.preview_slices==[]:
			# If no active display slices, just skip this whole function
			return
		self.master.click_x = event.x
		self.master.click_y = event.y
		return
		
	def canvas_right_drag(self,event):
		xmove = event.x-self.master.click_x
		ymove = event.y-self.master.click_y
		# Windowing is applied to the series as a whole...
		# Sensitivity needs to vary with the float pixel scale.  Map default window
		# (i.e. full range of image) to "sensitivity" px motion => 1px up/down adjusts level by
		# "default_window/sensitivity".  1px left/right adjusts window by
		# "default_window/sensitivity"
		window_sensitivity = 200
		level_sensitivity = 200
		min_window = self.master.fullrange/255
		i = self.master.active_slice
		self.master.temp_window = self.master.window+xmove*(self.master.fullrange/window_sensitivity)
		self.master.temp_level = self.master.level-ymove*(self.master.fullrange/level_sensitivity)
		if self.master.temp_window<min_window:
			self.master.temp_window=min_window
		if self.master.temp_level<self.master.global_rangemin+min_window/2:
			self.master.temp_level=self.master.global_rangemin+min_window/2
		self.master.preview_slices[i].wl_and_display(window=self.master.temp_window,level=self.master.temp_level)
		self.refresh_preview_image()
		return
		
	def canvas_right_click_release(self,event):
		print "RIGHT MOUSE RELEASED!"
		if abs(self.master.click_x-event.x)<1 and abs(self.master.click_y-event.y)<1:
			return
		self.master.window = self.master.temp_window
		self.master.level = self.master.temp_level
		#~ i=0
		for image in self.master.preview_slices:
			#~ self.progress(100.*i/len(self.master.preview_slices))
			image.wl_and_display(window=self.master.window,level=self.master.level)
			#~ i+=1
		self.refresh_preview_image()
		#~ self.progress(0.)
		return
		
	
	def asktoexit(self):
		if tkMessageBox.askokcancel("Quit?", "Are you sure you want to exit?"):
			#self.master.destroy()
			sys.exit()
		return
		
	def dir_window_selection(self,event):
		print "Selection made"
		selection = self.master.dirframe.dicomtree.selection()
		if not len(selection)==1:
			self.reset_small_canvas()
		else:
			parent_item = self.master.dirframe.dicomtree.parent(selection[0])
			if parent_item=='':
				# Whole study, so just reset the canvas
				self.reset_small_canvas()
			elif self.master.dirframe.dicomtree.parent(parent_item)=='':
				# Whole series, load all slices
				self.active_uids = self.master.dirframe.dicomtree.get_children(selection[0])
				self.load_preview_images(self.active_uids)
			else:
				# Single image, load single slice
				self.active_uids=(selection)
				self.load_preview_images(self.active_uids)
		return
			
	def progress(self,percentage):
		self.master.progressbar['value']=percentage
		self.master.progressbar.update()
		
	def load_preview_images(self, uid_array):
		"""
		Requires an array of unique instance UID's to search for in self.tag_list
		"""
		self.reset_small_canvas()
		n = 0
		for tag in self.sorted_list:
			if tag['instanceuid'] in uid_array:
				self.progress(50.*n/len(uid_array))
				if not tag['enhanced']:
					print tag['path']
					print type(tag['path'])
					self.master.preview_slices.append(MIPPY_8bitviewer(tag['path']))
				else:
					ds = dicom.read_file(tag['path'])
					self.master.preview_slices.append(MIPPY_8bitviewer(get_frame_ds(ds,tag['instance'])))
				n+=1
		
		# Set default windowing
		self.master.global_min,self.master.global_max = get_global_min_and_max(self.master.preview_slices)
		self.master.global_rangemin = self.master.preview_slices[0].rangemin
		self.master.global_rangemax = self.master.preview_slices[0].rangemax
		self.master.fullrange = self.master.global_rangemax-self.master.global_rangemin
		self.master.default_window = self.master.global_max-self.master.global_min
		self.master.default_level = self.master.global_min + self.master.default_window/2
		self.master.level = self.master.default_level
		self.master.window = self.master.default_window
		#~ self.reset_window_level()
		
		for i in range(len(self.master.preview_slices)):
			self.progress(50.*i/len(self.master.preview_slices)+50)
			self.master.preview_slices[i].wl_and_display(window=self.master.window,level=self.master.level)
			#~ self.reset_window_level()
			# This resize command is just hard-wired in for now.  Will probably change if
			# I build in the ability to zoom.  That may not happen...
			self.master.preview_slices[i].resize(256,256)
		
		self.master.active_slice = 0
		self.refresh_preview_image()
		self.progress(0.)
		return
		
	def reset_window_level(self):
		for i in range(len(self.master.preview_slices)):
			self.progress(100.*i/len(self.master.preview_slices))
			self.master.preview_slices[i].wl_and_display(window=self.master.default_window,level=self.master.default_level)
		
		self.master.level = self.master.default_level
		self.master.window = self.master.default_window
		self.progress(0.)
		return
		
	def refresh_preview_image(self):
		# self.master.preview_slices = []
		# self.master.active_slice = None
		i = self.master.active_slice
		self.master.imcanvas.delete('all')
		self.master.imcanvas.create_image(0,0,anchor='nw',image=self.master.preview_slices[i].photoimage)
		return
		
	def module_window_click(self,event):
		print "You clicked on the module window."
		
	def load_image_directory(self):
		print "Load image directory"
		self.dicomdir = tkFileDialog.askdirectory(parent=self.master,initialdir=r"M:",title="Select image directory")
		if not self.dicomdir:
			return
		ask_recursive = tkMessageBox.askyesno("Search recursively?","Do you want to include all subdirectories?")
		#~ self.open_progress_window()
		self.path_list = []
		#~ self.master.progressbar['mode']='indeterminate'
		#~ self.master.progressbar.start()
		
		self.path_list = list_all_files(self.dicomdir,file_list=self.path_list,recursive=ask_recursive)
		#~ self.master.progressbar.stop()
		#~ self.master.progressbar['mode']='determinate'
		#~ self.master.progressbar['value']=0.
		self.filter_dicom_files()
		self.build_dicom_tree()
		#~ self.close_progress_window()
		return
		
	def filter_dicom_files(self):
		self.tag_list = []
		for p in self.path_list:
			self.progress(100*(float(self.path_list.index(p))/float(len(self.path_list))))
			tags = collect_dicomdir_info(p)
			if tags:
				self.tag_list.append(tags)
		self.master.progressbar['value']=0.
		return
		
	#~ def open_progress_window(self):
		#~ progress_root = Tk()
		#~ self.master.queue = queue.Queue()
		#~ progress_window = ProgressWindow(progress_root,self.master.queue,'indeterminate')
		#~ thread = threading.Thread(target=progress_window.mainloop())
		#~ thread.start()
		#~ thread.join()
		#~ return
		
	#~ def close_progress_window(self):
		#~ self.master.queue.put('FINISHED')
		#~ return
		
	def build_dicom_tree(self):
		print "function_started"
		# This should sort the list into your initial order for the tree - maybe implement a more customised sort if necessary?
		self.sorted_list = sorted(self.tag_list)
		
		#~ i=0
		print self.master.dirframe.dicomtree.get_children()
		try:
			for item in self.master.dirframe.dicomtree.get_children():
				self.master.dirframe.dicomtree.delete(item)
			print "Existing tree cleared"
		except Exception:
			print "New tree created"
			pass
		for scan in self.sorted_list:
			print "Adding to tree: "+scan['path']
			if not self.master.dirframe.dicomtree.exists(scan['studyuid']):
				#~ i+=1
				self.master.dirframe.dicomtree.insert('','end',scan['studyuid'],text='------',
												values=(scan['date'],scan['name'],scan['studydesc']))
			if not self.master.dirframe.dicomtree.exists(scan['seriesuid']):
				self.master.dirframe.dicomtree.insert(scan['studyuid'],'end',scan['seriesuid'],
											text='Series '+str(scan['series']).zfill(3),
											values=('','',scan['seriesdesc']))
			self.master.dirframe.dicomtree.insert(scan['seriesuid'],'end',scan['instanceuid'],
											text=str(scan['instance']).zfill(3),
											values=('','',''))
		self.master.dirframe.dicomtree.update()
		#~ self.master.progress = 100
		return
		
	def scan_modules_directory(self):
		self.module_list = []
		for folder in os.listdir(os.path.join(self.root_dir,'modules')):
			if not os.path.isdir(os.path.join(self.root_dir,'modules',folder)):
				continue
			file_list = os.listdir(os.path.join(self.root_dir,'modules',folder))
			if ('__init__.py' in file_list
				and 'module_main.py' in file_list
				and 'config' in file_list):
				cfg_file = os.path.join(self.root_dir,'modules',folder,'config')
				with open(cfg_file,'r') as file_object:
					module_info = pickle.load(file_object)
				self.module_list.append(module_info)
		self.module_list = sorted(self.module_list)
		try:
			for item in self.master.moduleframe.moduletree.get_children():
				self.master.moduleframe.moduletree.delete(item)
			print "Existing module tree cleared"
		except Exception:
			print "New module tree created"
			pass
		for module in self.module_list:
			self.master.moduleframe.moduletree.insert('','end',module_info['dirname'],
				text=module_info['name'],values=(module_info['description'],module_info['author']))
		
		#~ self.master.progress = 50.
		return
		
	def exit_program(self):
		self.asktoexit()
		return
		
	def load_wiki(self):
		print "Load wiki"
		webbrowser.open_new('https://sourceforge.net/p/mippy/wiki/Home/')
		return
		
	def display_version_info(self):
		print "Display version info"
		self.master.progressbar['value']=50.
		return
			
	def load_test_module(self):
		current_module = this_module = importlib.import_module("analysis_modules.test_module_1.module_main")
		current_module.load_module()
		return
		
	def load_selected_module(self):
		print "DO NOTHING!"
		try:
			moduledir = self.master.moduleframe.moduletree.selection()[0]
			active_module = importlib.import_module('modules.'+moduledir+'.module_main')
			active_module.execute(self.master,self.dicomdir,self.active_uids)
		except:
			print "Did you select a module?"
			pass
		#~ active_module.load_module()
		return
		
	#~ def thread_this(self,target_function):
		#~ thread = threading.Thread(target=target_function)
		#~ thread.start()
		#~ return
		
	#~ def check_queue(self):
		#~ while True:
			#~ try:
				#~ self.master.progress = 100
			#~ except queue.Empty:
				#~ self.master.after(100, self.check_queue)
				#~ break
		#~ return
		

class ThreadedTask(threading.Thread):
	def __init__(self,queue,target_function):
		threading.Thread.__init__(self)
		self.queue = queue
		
class ProgressWindow(Frame):
	def __init__(self,master,queue1,progressmode='indeterminate'):
		Frame.__init__(self,master)
		self.root = master
		self.root.title('Working...')
		self.queue = queue1
		self.msgtext = StringVar()
		self.msglabel = Label(self.root,textvariable=self.msgtext)
		self.progressbar = Progressbar(self.root,mode=progressmode)
		if self.progressbar['mode']=='indeterminate':
			self.progressbar.start()
		self.msglabel.pack()
		self.progressbar.pack()
		self.running = True
		self.periodic_call()
	
	def periodic_call(self):
		self.check_queue()
		if self.running:
			self._job = self.after(100,self.periodic_call)
	
	def check_queue(self):
		while self.queue.qsize():
			try:
				msg = self.queue.get(0)
				self.msgtext = msg
				if msg=='FINISHED':
					self.running = False
					if self.progressbar['mode']=='indeterminate':
						self.progressbar.stop()
					self.root.destroy()
			except queue.Empty:
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
root_path = os.getcwd()
if "nt" == os.name:
    root_window.wm_iconbitmap(bitmap = "source/images/brain_orange.ico")
else:
    root_window.wm_iconbitmap('@'+os.path.join(root_path,'source','images','brain_bw.xbm'))
#root_window.geometry("+50+50")
#root_window.wm_resizeable(False,False)
root_app = ToolboxHome(master = root_window)
#~ iconpath = os.path.join(os.getcwd(),'icon_orange.png')
#~ root_app.iconbitmap(iconpath)
#~ im_from_file = Image.open(iconpath)
#~ icon_img = PhotoImage(im_from_file)
#~ root_app.tk.call('wm', 'iconphoto', root_app._w, icon_img)

#~ print dir(mippy_modules)

#~ main_queue = queue.Queue()



root_app.mainloop()
