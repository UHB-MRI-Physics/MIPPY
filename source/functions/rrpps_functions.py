# -*- coding: utf-8 -*-
"""
RRPPS Functions

These are functions specific to integration with RRPPS processes.  For example,
accessing and manipulating the MRI QA results database, report templates etc.

Any more generally useful functions will be moved into other locations as they
develop. It is intended that "general purpose" MIPPY may be distributed without
the functions contained in this module.


Created on Tue Jan 03 11:18:45 2017

@author: Rob Flintham (robert.flintham@uhb.nhs.uk)
"""

import sqlite3
import dicom
import numpy as np
from Tkinter import *
from ttk import *


class QADatabase(object):
	"""
	This class provides an interface for connecting to the RRPPS MR QA
	database, which should ensure data gets stored appropriately.

	It uses the SQLITE3, NUMPY and PYDICOM modules.
	"""

	def __init__(self,path=None):
		if not path:
			# Use default path. Adjust how this is decided later.
			path=r'M:\QA\QA_database\QA_database_dev.db'
		self.path = path

	def get_scanners(self):
		conn = sqlite3.connect(self.path)
		c = conn.cursor()

		c.execute('SELECT ScannerID FROM Customer_Scanners')
		scanner_list = c.fetchall()
		conn.close()
		scanners = np.array(scanner_list).astype(str).flatten()
		return np.unique(scanners).tolist()

	def get_sites(self):
		conn = sqlite3.connect(self.path)
		c = conn.cursor()

		c.execute('SELECT Site FROM Customer_Scanners')
		site_list = c.fetchall()
		sites = np.array(site_list).astype(str).flatten()

		conn.close()
		return np.unique(sites).tolist()

	def get_scanners_at_site(self,site):
		conn = sqlite3.connect(self.path)
		c = conn.cursor()
		c.execute('SELECT ScannerID FROM Customer_Scanners WHERE Site=?',(site,))
		scannerID_list = c.fetchall()
		scannerIDs = np.unique(np.array(scannerID_list).astype(str).flatten())

		# Get descriptions of scanners

		descriptions = []
		for ID in scannerIDs:
			c.execute('SELECT ScannerManufacturer,ScannerModel,FieldStrength '+
			'FROM Customer_Scanners LEFT OUTER JOIN Scanner_Data '+
			'ON Customer_Scanners.ScannerModelCode = Scanner_Data.ScannerModelCode '+
			'WHERE ScannerID=?',(ID,))
			first = c.fetchone()
			descriptions.append(first[0]+" "+first[1]+" "+str(np.round(first[2],1))+"T")

		scanner_descriptions = np.array(descriptions).astype(str).flatten()

		conn.close()
		return scannerIDs.tolist(),scanner_descriptions.tolist()

	def get_coils_on_scanner(self,scanner):
		conn = sqlite3.connect(self.path)
		c = conn.cursor()

		c.execute('SELECT Coil FROM Full_QA_Table WHERE ScannerID=?',(scanner,))

		coil_list = c.fetchall()
		conn.close()
		coils = np.array(coil_list).astype(str).flatten()
		return np.unique(coils).tolist()

	def save_results(self,scanner,date,coil,test,result,bandwidth,
				notes=None,uni_corr=None,geo_corr=None,noi_filt=None,
				replace=False):
		conn = sqlite3.connect(self.path)
		c = conn.cursor()

		# Test if result already exists
		testvalues = (scanner,date,coil,test)
		c.execute('SELECT TestRepeat FROM Full_QA_Table '+
		'WHERE ScannerID=? AND Date=? AND Coil=? AND Test=?',testvalues)
		existing = c.fetchall()
		repeat = str(len(existing)+1).zfill(3)
		data_to_insert = (scanner,date,coil,test,result,repeat,notes,bandwidth,
					uni_corr,geo_corr,noi_filt)
		c.execute('INSERT INTO Full_QA_Table VALUES (?,?,?,?,?,?,?,?,?,?,?)',data_to_insert)
		conn.commit()
		conn.close()
		return

	def popup_save(self,master_window):
		saver = Toplevel(master_window)
		saver.site_label = Label(saver,text='Please select the site:')
		saver.scanner_label = Label(saver,text='Please select the scanner:')
		saver.replace_label = Label(saver,text='Replace existing results? (if available)')

#		# Connect to database to read contents
#		conn = sqlite3.connect(self.path)
#		c = conn.cursor()

		# Get site list
		saver.sites = self.get_sites()


		# Get scanners at each site
		saver.scanners_by_site = []
		saver.descs_by_site = []
		for site in saver.sites:
			scanners,descriptions = self.get_scanners_at_site(site)
			saver.scanners_by_site.append(scanners)
			saver.descs_by_site.append(descriptions)



		# Set up option menus
		saver.sites_v = StringVar(saver)
		saver.scanners_v = StringVar(saver)
		saver.site_choice = OptionMenu(saver,saver.sites_v,saver.sites[0],*saver.sites,command=lambda _:self.update_scanner_options(saver))
		saver.scanner_choice = OptionMenu(saver,saver.scanners_v,'')
		saver.site_label.grid(row=0,column=0)
		saver.site_choice.grid(row=0,column=1)
		saver.scanner_label.grid(row=1,column=0)
		saver.scanner_choice.grid(row=1,column=1)
		self.update_scanner_options(saver)
		return

	def update_scanner_options(self,win):
		site = win.sites_v.get()
		site_index = win.sites.index(site)
		win.scanner_choice['menu'].delete(0,'end')
		for choice in win.scanners_by_site[site_index]:
			win.scanner_choice['menu'].add_command(label=choice, command=win.scanners_v.set(choice))
		win.scanners_v.set(win.scanners_by_site[site_index][0])
		win.update()
		return








