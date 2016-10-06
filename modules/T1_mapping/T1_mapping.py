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
def inv_recovery(TI,M0,T1):
    return abs(M0*(1-(2*np.exp(-TI/T1))))

###################################################


###################################################
# MAIN BODY OF PROGRAM
###################################################

def T1_mapping(Im4D,TI,images,rev=False):
    outputdir = "maps"

    rows=np.size(Im4D,2)
    cols=np.size(Im4D,3)
    slcs=np.size(Im4D,1)
    dyns=np.size(Im4D,0)										

    T1_map = np.zeros((slcs,rows,cols))
    T1_var = np.zeros((slcs,rows,cols))
    T1_R2 = np.zeros((slcs,rows,cols))
    M0_map = np.zeros((slcs,rows,cols))
    M0_var = np.zeros((slcs,rows,cols))

    T1 = float(500)
    #tolerance = 0.1
								
    threshold = 0.1*np.mean(np.fabs(Im4D))
#    threshold = 0
    # print threshold

    for s in range(slcs):		                            							    
        print "Fitting slice "+str(s+1)+" of "+str(slcs)
        for y in range(rows):
            print "..."+str(int((float(y)/float(rows))*100))+"%"
            for x in range(cols):
                if np.amax(np.fabs(Im4D[:,s,y,x]))<threshold:
                    T1_map[s,y,x] = 0
                    T1_var[s,y,x] = 0
                    T1_R2[s,y,x] = 0
                    M0_map[s,y,x]=0
                    M0_var[s,y,x]=0
##                    print "below threshold"
                    continue
                popt = float(0)	
                pcov = float(0)
                xdata = float(0)
                ydata = float(0)
                
                try:
                    """
                    What actually happens here varies depending in what sort of mapping type was selected, but all essentially the same process.
                    Collect available x-data (TI or TE) from array and corresponding y-data (signal values).  Pass variables to curve_fit function
                    which spits out optimised fit parameters along with a covariance matrix - diagonals of covariance matrix are the variance
                    of each fit parameter.
                    """
##                    xdata = np.trim_zeros(TI[:,s,y,x],'b')
                    xdata = TI[s::dyns-1]
                    ydata = Im4D[0:len(xdata),s,y,x]
                    T1 = -xdata[np.argmin(ydata)]/np.log(0.5)
                    M0 = 1.2*np.amax(ydata)
                    popt,pcov = curve_fit(inv_recovery,xdata,ydata,p0=[M0,T1])

                    if not isinstance(pcov,float):                                                                                  # Checks to make sure covariance matrix is actually a matrix.  A failed fit gives a floating point "inf" value instead.
                        T1_map[s,y,x] = popt[1]
                        M0_map[s,y,x] = popt[0]
                        T1_var[s,y,x] = pcov[1,1]
                        M0_var[s,y,x] = pcov[0,0]
                        
                        fit = inv_recovery(xdata,popt[0],popt[1])
                        
                        mean = np.mean(ydata)
                        SSres = np.sum((fit - ydata)**2)
                        SStot = np.sum((mean - ydata)**2)
##                        T1_R2[s,y,x] = 1 - (SSres/SStot)
                        T1_R2[s,y,x] = 100 - np.mean(abs(ydata-fit))/(np.max(ydata)-np.min(ydata))*100
##                        print T1_R2[s,y,x]
    #                    if R2[s,y,x]>0.99:
    #                        T1 = T2 = T2star = popt[1]
    #                        M0 = popt[0]

    ##                    print popt[1],M0/np.amax(ydata),T1_R2[s,y,x]
                        
                    else:                                                                                                                   # If fit failed and just "inf" exists instead of a covariance matrix, ignore the point, set the result and other parameters to zero
                        T1_var[s,y,x] = 0
                        T1_map[s,y,x] = 0
                        T1_R2[s,y,x] = 0
                        M0_map[s,y,x] = 0
                        M0_var[s,y,x] = 0
                        print "Fit failed, no optimised parameters"
                        
                    if T1_R2[s,y,x]<70:
                        T1_map[s,y,x] = 0
                        T1_var[s,y,x] = 0
                        T1_R2[s,y,x] = 0                                                                                                   # If calculated variance on result is larger than the result, also ignore and set to zero
                        M0_map[s,y,x] = 0
                        M0_var[s,y,x] = 0
                        print "goodness of fit < 70%"
##                        x_fit=np.array(range(0,int(np.round(np.amax(xdata),0))+10))
##                        plt.errorbar(xdata,ydata,marker='o',linestyle='None',color='blue')
##                        plt.errorbar(x_fit,inv_recovery(x_fit,popt[0],popt[1]),marker='None',linestyle='-',color='blue')
##                        plt.show()
                        
                    # SSres = sum of square distances from fit
                    # SStot = sum of square distances from mean
                    # R2 = 1 - (SSres/SStot)
                    
                except Exception, e:
                
                    print str(e)
                    T1_map[s,y,x]=0
                    T1_var[s,y,x]=0
                    T1_R2[s,y,x] = 0                                                                                                          # If fitting fails for some other reason, also set result to zero
                    M0_map[s,y,x] = 0
                    M0_var[s,y,x] = 0
                    print "Unspecified exception"


##                if x==32 and y==48 and s==4:
##                    x_fit=np.array(range(0,int(np.round(np.amax(xdata),0))+10))
##                    plt.errorbar(xdata,ydata,marker='o',linestyle='None',color='blue')
##                    plt.errorbar(x_fit,inv_recovery(x_fit,popt[0],popt[1]),marker='None',linestyle='-',color='blue')
##                    plt.show()

    #   clip R2 to a range of 0 to 1.  Negative numbers are meaningless.

        T1_R2 = np.clip(T1_R2,0,100)

    return T1_map,T1_R2,T1_var,M0_map,M0_var
