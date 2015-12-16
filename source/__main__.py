print "Importing packages..."
print "    DICOM"
import dicom
print "    Tkinter (GUI)"
import tkMessageBox
from Tkinter import *
from ttk import *
print "    os"
import os
print "    NumPy"
import numpy as np
print "    Python Imaging Library (PIL)"
from PIL import Image, ImageTk
print "    math"
from math import floor
print "    easyGUI"
from easygui import diropenbox, codebox
print "    date/time"
import datetime
import time
print "    SciPy"
from scipy.signal import convolve2d
from scipy.ndimage.measurements import center_of_mass
from scipy.ndimage.filters import convolve
from scipy.ndimage import map_coordinates
from scipy.optimize import curve_fit
import importlib
import sys

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
		
		self.master.test_button_1 = Button(master, text="Test button 1",command=lambda:self.load_test_module())
		self.master.test_button_2 = Button(master, text="Test button 2")
		
		self.master.test_button_1.grid(row=0,column=0,sticky='nsew')
		self.master.test_button_2.grid(row=0,column=1,sticky='nsew')
		
		self.master.rowconfigure(0,weight=1)
		self.master.columnconfigure(0,weight=1)
		self.master.columnconfigure(1,weight=1)
		
		master.focus()
		
			
	def asktoexit(self):
		if tkMessageBox.askokcancel("Quit?", "Are you sure you want to exit?"):
			#self.master.destroy()
			sys.exit()
		return
		
	def load_image_directory(self):
		print "Load image directory"
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
		
		

#########################################################
"""
Here is where the program is actually executed.  "root_window" Tk() object is created (Tk is 
the GUI package), then given a title and dimensions as attributes, then used to create the
"ToolboxHome" application.  The "mainloop" function then enters the actual application.
"""

root_window = Tk()
root_window.title("Python Image Analysis Toolbox")
#root_window.geometry("+50+50")
#root_window.wm_resizeable(False,False)
root_app = ToolboxHome(master = root_window)
root_app.mainloop()