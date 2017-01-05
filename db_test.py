# -*- coding: utf-8 -*-
"""
Created on Tue Jan 03 12:30:07 2017

@author: rtfm
"""

import source.functions.rrpps_functions as rrpps
import numpy as np
from Tkinter import *
from ttk import *

def callbackfunc(*args, **kwargs):
	print(args,kwargs)

class App(object):
	def __init__(self, master):
		frame = Frame(master)
		frame.pack()
		db = rrpps.QADatabase()
		db.popup_save(master)

root = Tk()
app = App(root)
root.mainloop()