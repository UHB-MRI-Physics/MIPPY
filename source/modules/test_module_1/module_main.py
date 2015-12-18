from Tkinter import *
from ttk import *
import tkMessageBox

import functions.rf_basics as imfunc



class TestModule(Frame):
	
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
		master.protocol("WM_DELETE_WINDOW", self.asktoexit)
		
		self.master.test_button_1 = Button(master, text="Test button 1",command=lambda:self.test_imfunc())
		self.master.test_button_2 = Button(master, text="Test button 2")
		
		self.master.test_button_1.grid(row=0,column=0,sticky='nsew')
		self.master.test_button_2.grid(row=0,column=1,sticky='nsew')
		
		self.master.rowconfigure(0,weight=1)
		self.master.columnconfigure(0,weight=1)
		self.master.columnconfigure(1,weight=1)
		
		master.focus()
	
	def asktoexit(self):
		if tkMessageBox.askokcancel("Quit?", "Are you sure you want to close this module?"):
			self.master.destroy()
	
	def test_imfunc(self):
		result = imfunc.add(1,2)
		tkMessageBox.showinfo("The result is "+str(result))
		return


def load_module():
	test_analysis_root = Tk()
	test_analysis_root.title("Test analysis module")
	test_app = TestModule(master = test_analysis_root)
	test_app.mainloop()
	return