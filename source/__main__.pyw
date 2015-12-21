"""
Icon attribution:
Icon made by Freepik from www.flaticon.com
"""

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
from datetime import datetime
import time
#~ print "    SciPy"
#~ from scipy.signal import convolve2d
#~ from scipy.ndimage.measurements import center_of_mass
#~ from scipy.ndimage.filters import convolve
#~ from scipy.ndimage import map_coordinates
#~ from scipy.optimize import curve_fit
import importlib
import sys
from functions.file_functions import *
import ScrolledText
import webbrowser
from functions.viewer_functions import *

print "Initialising GUI...\n"

class RedirectText(object):
	""""""
	#----------------------------------------------------------------------
	def __init__(self, text_ctrl, log):
		"""Constructor"""
		self.output = text_ctrl
		self.logfile = log
	#----------------------------------------------------------------------
	def write(self, string):
		""""""
		self.output.insert(END, string)
		with open(self.logfile,'a') as f:
			f.write('\n'+string)


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
		
		# Add capture for stdout and stderr output for log file, and scrollable text box
		self.master.logoutput = ScrolledText.ScrolledText(self.master,height=6)
		redir_out = RedirectText(self.master.logoutput,logpath)
		redir_err = RedirectText(self.master.logoutput,logpath)
		sys.stdout = redir_out
		sys.stderr = redir_err
		
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
		
		
		
		
		# Create module treeview
		self.master.moduleframe.moduletree = Treeview(self.master.moduleframe)
		
		# Use grid to position module list in frame
		self.master.moduleframe.moduletree.grid(row=0,column=0,sticky='nsew')
		
		# Configure column and row weights (relative stretchability when resizing)
		self.master.moduleframe.rowconfigure(0,weight=1)
		self.master.moduleframe.columnconfigure(0,weight=1)
		
		# Bind "module select" event to required action
		self.master.moduleframe.moduletree.bind('<<TreeviewSelect>>',self.module_window_click)
		
		# Just adding a random line to the tree for testing
		self.master.moduleframe.moduletree.insert('','end',"test row",text="Blah blah",values=("Option 1","Option 2"))
				
		# Create canvas object to draw images in
		self.master.imcanvas = Canvas(self.master,bd=0,width=256, height=256)
		self.reset_small_canvas()
		
		# Bind methods for window and level to canvas (right mouse click)
		self.master.imcanvas.bind('<Button-3>',self.canvas_right_click)
		self.master.imcanvas.bind('<B3-Motion>',self.canvas_right_drag)
		self.master.imcanvas.bind('<Double-Button-3>',self.canvas_right_doubleclick)
		self.master.imcanvas.bind('<ButtonRelease-3>',self.canvas_right_click_release)
		
		# Create button to control image scrolling
		self.master.scrollbutton = Button(self.master, text="SLICE + / -")
		self.master.scrollbutton.bind('<Button-1>',self.slice_scroll_button_click)
		self.master.scrollbutton.bind('<B1-Motion>',self.slice_scroll_button_drag)
		
		# Create buttons:
		# "Load module"
		self.master.loadmodulebutton = Button(self.master,text="Load module",command=lambda:self.load_selected_module())
		
		# Set up logfile in logs directory
		logpath=os.path.join(os.getcwd(),"logs",str(datetime.now()).replace(":",".").replace(" ","_")+".txt")
		with open(logpath,'w') as logout:
			logout.write('LOG FILE\n')
		
		
		
		
		
		# Use "grid" to position objects within "master"
		self.master.dirframe.grid(row=0,column=0,columnspan=2,rowspan=1,sticky='nsew')
		self.master.imcanvas.grid(row=1,column=0,sticky='nsew')
		self.master.moduleframe.grid(row=1,column=1,sticky='nsew')
		self.master.loadmodulebutton.grid(row=2,column=1,sticky='nsew')
		self.master.scrollbutton.grid(row=2,column=0,sticky='nsew')
		self.master.logoutput.grid(row=3,column=0,rowspan=1,columnspan=2,sticky='nsew')
		
		# Set row and column weights to handle resizing
		self.master.rowconfigure(0,weight=1)
		self.master.rowconfigure(1,weight=0)
		self.master.rowconfigure(2,weight=0)
		self.master.rowconfigure(3,weight=0)
		self.master.columnconfigure(0,weight=0)
		self.master.columnconfigure(1,weight=1)
		
		master.focus()
	
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
		sensitivity=20
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
		
	def canvas_right_doubleclick(self,event):
		if self.master.preview_slices == []:
			return
		
		self.master.temp_window = self.master.default_window
		self.master.temp_level = self.master.default_level
		self.master.window = self.master.default_window
		self.master.level = self.master.default_level
		
		for image in self.master.preview_slices:
			image.wl_control(window = self.master.default_window, level = self.master.default_level)
		
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
		window_sensitivity = 100
		level_sensitivity = 100
		min_window = self.master.fullrange/255
		i = self.master.active_slice
		self.master.temp_window = self.master.window+xmove*(self.master.fullrange/window_sensitivity)
		self.master.temp_level = self.master.level-ymove*(self.master.fullrange/level_sensitivity)
		if self.master.temp_window<min_window:
			self.master.temp_window=min_window
		if self.master.temp_level<self.master.global_rangemin+min_window/2:
			self.master.temp_level=self.master.global_rangemin+min_window/2
		self.master.preview_slices[i].wl_control(window=self.master.temp_window,level=self.master.temp_level)
		self.refresh_preview_image()
		return
		
	def canvas_right_click_release(self,event):
		print "RIGHT MOUSE RELEASED!"
		if abs(self.master.click_x-event.x)<1 and abs(self.master.click_y-event.y)<1:
			return
		self.master.window = self.master.temp_window
		self.master.level = self.master.temp_level
		for image in self.master.preview_slices:
			image.wl_control(window=self.master.window,level=self.master.level)
		self.refresh_preview_image()
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
				self.load_preview_images(self.master.dirframe.dicomtree.get_children(selection[0]))
			else:
				# Single image, load single slice
				self.load_preview_images(selection)
		return
			
		
	def load_preview_images(self, uid_array):
		"""
		Requires an array of unique instance UID's to search for in self.tag_list
		"""
		self.reset_small_canvas()
		
		for tag in self.sorted_list:
			if tag['instanceuid'] in uid_array:
				if not tag['enhanced']:
					print tag['path']
					print type(tag['path'])
					self.master.preview_slices.append(MIPPY_8bitviewer(tag['path']))
				else:
					ds = dicom.read_file(tag['path'])
					self.master.preview_slices.append(MIPPY_8bitviewer(split_enhanced_dicom(ds,tag['instance'])))
		
		# Set default windowing
		self.master.global_min,self.master.global_max = get_global_min_and_max(self.master.preview_slices)
		self.master.global_rangemin = self.master.preview_slices[0].rangemin
		self.master.global_rangemax = self.master.preview_slices[0].rangemax
		self.master.fullrange = self.master.global_rangemax-self.master.global_rangemin
		self.master.default_window = self.master.global_max-self.master.global_min
		self.master.default_level = self.master.global_min + self.master.default_window/2
		
		for i in range(len(self.master.preview_slices)):
			self.reset_window_level()
			# This resize command is just hard-wired in for now.  Will probably change if
			# I build in the ability to zoom.  That may not happen...
			self.master.preview_slices[i].resize(256,256)
		
		self.master.active_slice = 0
		self.refresh_preview_image()
		return
		
	def reset_window_level(self):
		for i in range(len(self.master.preview_slices)):
			self.master.preview_slices[i].wl_control(window=self.master.default_window,level=self.master.default_level)
		
		self.master.level = self.master.default_level
		self.master.window = self.master.default_window
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
		dicomdir = tkFileDialog.askdirectory(parent=self.master,initialdir=r"M:",title="Select image directory")
		if not dicomdir:
			return
		ask_recursive = tkMessageBox.askyesno("Search recursively?","Do you want to include all subdirectories?")
		print dicomdir
		print ask_recursive
		self.path_list = []
		print self.path_list
		self.path_list = list_all_files(dicomdir,self.path_list,recursive=ask_recursive)
		print self.path_list
		self.build_dicom_tree()		
		return
		
	def build_dicom_tree(self):
		# Build tree by first organising list - inspecting study UID, series UID, instance number
		self.tag_list = []
		
		for p in self.path_list:
			# This automatically excludes Philips "XX_" files, but only based on name.  If they've been renamed they
			# won't be picked up until the "try/except" below.
			if os.path.split(p)[1].startswith("XX_"):
				continue
			
			# Remove any previous datasets just held as "ds" in memory
			ds = None
			#Read file, if not DICOM then ignore
			try:
				ds = dicom.read_file(p)				
			except Exception:
				print p+'\n...is not a valid DICOM file and is being ignored.'
				continue
			if ds:
				try:
					# There has to be a better way of testing this...?
					# If "ImageType" tag doesn't exist, then it's probably an annoying "XX" type file from Philips
					type = ds.ImageType
				except Exception:
					continue
				seriesdesc = ds.SeriesDescription
				if "PHOENIXZIPREPORT" in seriesdesc.upper():
					# Ignore any phoenix zip report files from Siemens
					continue
				# Unless told otherwise, assume normal MR image storage
				mode = "Assumed MR Image Storage"
				try:
					mode = str(ds.SOPClassUID)
				except Exception:
					pass
				if "SOFTCOPY" in mode.upper() or "BASIC TEXT" in mode.upper():
					# Can't remember why I have these, I think they're possible GE type files???
					continue
				if mode.upper()=="ENHANCED MR IMAGE STORAGE":
					# If enhanced file, record number of frames.  This is important for pulling the right imaging
					# data out for the DICOM tree and image previews
					enhanced = True
					frames = ds.NumberOfFrames
				else:
					enhanced = False
					frames = 1
				study_uid = ds.StudyInstanceUID
				series_uid = ds.SeriesInstanceUID
				name = ds.PatientName
				date = ds.StudyDate
				series = ds.SeriesNumber
				time = ds.StudyTime
				try:
					# Some manufacturers use a handy "study description" tag, some don't
					studydesc = ds.StudyDescription
				except Exception:
					try:
						# Philips stores "body part examined", which will do for now until I find something better
						studydesc = ds.BodyPartExamined
					except Exception:
						# If all else fails, just use a generic string
						studydesc = "Unknown Study Type"
				if enhanced:
					# Set "instance" array to match number of frames
					instance = np.array(range(frames))+1
				else:
					# Of if not enhanced/multi-frame, just create a single element list so that the code
					# below still works
					instance = [ds.InstanceNumber]
				
				for i in instance:
					if not enhanced:
						instance_uid = ds.SOPInstanceUID
					else:
						# Append instance UID with the frame number to give unique reference to each slice
						instance_uid = ds.SOPInstanceUID+"_"+str(i).zfill(3)
					# Append the information to the "tag list" object
					self.tag_list.append(dict([('date',date),('time',time),('name',name),('studyuid',study_uid),
									('series',series),('seriesuid',series_uid),('studydesc',studydesc),
									('seriesdesc',seriesdesc),('instance',i),('instanceuid',instance_uid),
									('path',p),('enhanced',enhanced)]))
		
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
		return
		
		
	def refresh_directory(self):
		print "Refresh directory"
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
		return
			
	def load_test_module(self):
		current_module = this_module = importlib.import_module("analysis_modules.test_module_1.module_main")
		current_module.load_module()
		return
		
	def load_selected_module(self):
		print "DO NOTHING!"
		return
		
		

#########################################################
"""
Here is where the program is actually executed.  "root_window" Tk() object is created (Tk is 
the GUI package), then given a title and dimensions as attributes, then used to create the
"ToolboxHome" application.  The "mainloop" function then enters the actual application.
"""

root_window = Tk()
root_window.title("MIPPY: Modular Image Processing in Python")
root_window.minsize(650,400)
if "nt" == os.name:
    root_window.wm_iconbitmap(bitmap = "images/brain_orange.ico")
else:
    root_window.wm_iconbitmap(bitmap = "images/brain_bw.xbm")
#root_window.geometry("+50+50")
#root_window.wm_resizeable(False,False)
root_app = ToolboxHome(master = root_window)
#~ iconpath = os.path.join(os.getcwd(),'icon_orange.png')
#~ root_app.iconbitmap(iconpath)
#~ im_from_file = Image.open(iconpath)
#~ icon_img = PhotoImage(im_from_file)
#~ root_app.tk.call('wm', 'iconphoto', root_app._w, icon_img)



root_app.mainloop()
