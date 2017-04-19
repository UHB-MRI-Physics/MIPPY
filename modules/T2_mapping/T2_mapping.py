import numpy as np
import scipy as sp
from scipy.optimize import curve_fit
import dicom
from easygui import msgbox, diropenbox, choicebox, multenterbox
import os
import sys
from subprocess import call
import Tkinter
import ttk
import matplotlib.pyplot as plt

###################################################
"""
Functions here define functions to be fitted.  They must take "x" values as first input followed by
all additional variables to be fitted, returning "y" values (in the form of transformed/manipulated
array of "x" values).
"""
def T2_decay(TE,M0,T2):
	return abs(M0*np.exp(-TE/T2))

###################################################


###################################################
# MAIN BODY OF PROGRAM
###################################################

def T2_mapping(Im4D,TE,images,threshold,GoF):
	outputdir = "maps"

	rows=np.size(Im4D,2)
	cols=np.size(Im4D,3)
	slcs=np.size(Im4D,1)
	dyns=np.size(Im4D,0)

	T2_map = np.zeros((slcs,rows,cols))
	T2_var = np.zeros((slcs,rows,cols))
	T2_R2 = np.zeros((slcs,rows,cols))
	M0_map = np.zeros((slcs,rows,cols))
	M0_var = np.zeros((slcs,rows,cols))

	T2 = float(50)
	#tolerance = 0.1
								
	threshold = 0.05*np.amax(np.fabs(Im4D))

	# print threshold

	for s in range(slcs):
		print "Fitting slice "+str(s+1)+" of "+str(slcs)
		print TE[s::slcs]
		for y in range(rows):
			print "..."+str(int((float(y)/float(rows))*100))+"%"
			for x in range(cols):
				if np.amax(np.fabs(Im4D[:,s,y,x]))<threshold:
					T2_map[s,y,x] = 0
					T2_var[s,y,x] = 0
					T2_R2[s,y,x] = 0
					M0_map[s,y,x]=0
					M0_var[s,y,x]=0
					continue

				popt = float(0)
				pcov = float(0)
				xdata = float(0)
				ydata = float(0)

				try:
					"""
					What actually happens here varies depending in what sort of mapping type was selected, but all essentially the same process.
					Collect available x-data (TI or TE) from array and corresponding y-data (signal values).Pass variables to curve_fit function
					which spits out optimised fit parameters along with a covariance matrix - diagonals of covariance matrix are the variance
					of each fit parameter.
					"""
					xdata = TE[s::slcs]
					ydata = Im4D[0:len(xdata),s,y,x]
					T2 = 5.
					M0 = 1.2*np.amax(ydata)
					popt,pcov = curve_fit(T2_decay,xdata,ydata,p0=[M0,T2])

					if not isinstance(pcov,float):
						# Checks to make sure covariance matrix is actually a matrix.  A failed fit gives a floating point "inf" value instead.
						T2_map[s,y,x] = popt[1]
						M0_map[s,y,x] = popt[0]
						T2_var[s,y,x] = pcov[1,1]
						M0_var[s,y,x] = pcov[0,0]

						fit = T2_decay(xdata,popt[0],popt[1])

						mean = np.mean(ydata)
						SSres = np.sum((fit - ydata)**2)
						SStot = np.sum((mean - ydata)**2)

						T2_R2[s,y,x] = 100 - np.mean(abs(ydata-fit))/(np.max(ydata)-np.min(ydata))*100

					else:
						# If fit failed and just "inf" exists instead of a covariance matrix, ignore the point, set the result and other parameters to zero
						T2_var[s,y,x] = 0
						T2_map[s,y,x] = 0
						T2_R2[s,y,x] = 0
						M0_map[s,y,x] = 0
						M0_var[s,y,x] = 0
						print "Fit failed, no optimised parameters"

					if T2_R2[s,y,x]<50:
						T2_map[s,y,x] = 0
						T2_var[s,y,x] = 0
						T2_R2[s,y,x] = 0
						# If calculated variance on result is larger than the result, also ignore and set to zero
						M0_map[s,y,x] = 0
						M0_var[s,y,x] = 0
						print "goodness of fit < 50%"

				except Exception, e:

					print str(e)
					T2_map[s,y,x]=0
					T2_var[s,y,x]=0
					T2_R2[s,y,x] = 0
					# If fitting fails for some other reason, also set result to zero
					M0_map[s,y,x] = 0
					M0_var[s,y,x] = 0
					print "Unspecified exception"


		#clip R2 to a range of 0 to 1. Negative numbers are meaningless.

		T2_R2 = np.clip(T2_R2,0,100)

	return T2_map,T2_R2,T2_var,M0_map,M0_var
