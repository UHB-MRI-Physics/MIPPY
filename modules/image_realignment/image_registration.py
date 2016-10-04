import numpy as np
import scipy as sp
from scipy.optimize import curve_fit
from scipy.ndimage.interpolation import rotate
from scipy.ndimage.interpolation import shift
from scipy.optimize import minimize
import dicom
from easygui import msgbox, diropenbox, choicebox, multenterbox
import os
import sys
from subprocess import call
import time

def search_directory(dirs):
    """Function recursively searches input directory and appends found images
    to list of files.  Ignores if can't be read as DICOM."""
    print 'Searching directory:\n'+str(dirs)
    temp_file_list = os.listdir(dirs)
    for f in temp_file_list:
        path = os.path.join(dirs, f)
        if os.path.isdir(path):
            pass
        else:
            try:
                ds = dicom.read_file(path)
                file_list.append(path)
            except:
                continue

def search_min(fits,Im_in,Im_ref,edge):
    Im_in_=rotate(Im_in,fits[3],axes=(0,1), reshape=False)
    Im_in_=rotate(Im_in_,fits[4],axes=(0,2), reshape=False)
    Im_in_=rotate(Im_in_,fits[5],axes=(1,2), reshape=False)
    Im_in_=shift(Im_in_,[fits[0],fits[1],fits[2]])
    Im_in_edge=make_edges(Im_in_)
    Im_in_ref_edge=make_edges(Im_ref)
#    print np.sum((Im_ref-Im_in_)*(Im_ref-Im_in_))
    return np.sum((100-edge)*(Im_ref-Im_in_)*(Im_ref-Im_in_)
                  +edge*(Im_in_ref_edge-Im_in_edge)*(Im_in_ref_edge-Im_in_edge))

def search_min_Tx(Tx,Im_in,Im_ref,edge):
    Im_in_=shift(Im_in,[Tx,0,0])
    Im_in_edge=make_edges(Im_in_)
    Im_in_ref_edge=make_edges(Im_ref)
#    print np.sum((Im_ref-Im_in_)*(Im_ref-Im_in_))
    return np.sum((100-edge)*(Im_ref-Im_in_)*(Im_ref-Im_in_)
                  +edge*(Im_in_ref_edge-Im_in_edge)*(Im_in_ref_edge-Im_in_edge))

def search_min_Ty(Ty,Im_in,Im_ref,edge):
    Im_in_=shift(Im_in,[0,Ty,0])
    Im_in_edge=make_edges(Im_in_)
    Im_in_ref_edge=make_edges(Im_ref)
#    print np.sum((Im_ref-Im_in_)*(Im_ref-Im_in_))
    return np.sum((100-edge)*(Im_ref-Im_in_)*(Im_ref-Im_in_)
                  +edge*(Im_in_ref_edge-Im_in_edge)*(Im_in_ref_edge-Im_in_edge))

def search_min_Tz(Tz,Im_in,Im_ref,edge):
    Im_in_=shift(Im_in,[0,0,Tz])
    Im_in_edge=make_edges(Im_in_)
    Im_in_ref_edge=make_edges(Im_ref)
#    print np.sum((Im_ref-Im_in_)*(Im_ref-Im_in_))
    return np.sum((100-edge)*(Im_ref-Im_in_)*(Im_ref-Im_in_)
                  +edge*(Im_in_ref_edge-Im_in_edge)*(Im_in_ref_edge-Im_in_edge))

def search_min_x(alpha,Im_in,Im_ref,edge):
    Im_in_=rotate(Im_in,alpha,axes=(0,1),reshape=False)
    Im_in_edge=make_edges(Im_in_)
    Im_in_ref_edge=make_edges(Im_ref)
    
#    print np.sum((Im_ref-Im_in_)*(Im_ref-Im_in_))
    return np.sum((100-edge)*(Im_ref-Im_in_)*(Im_ref-Im_in_)
                  +edge*(Im_in_ref_edge-Im_in_edge)*(Im_in_ref_edge-Im_in_edge))

def search_min_y(beta,Im_in,Im_ref,edge):
    Im_in_=rotate(Im_in,beta,axes=(0,2),reshape=False)
    Im_in_edge=make_edges(Im_in_)
    Im_in_ref_edge=make_edges(Im_ref)
#    print np.sum((Im_ref-Im_in_)*(Im_ref-Im_in_))
    return np.sum((100-edge)*(Im_ref-Im_in_)*(Im_ref-Im_in_)
                  +edge*(Im_in_ref_edge-Im_in_edge)*(Im_in_ref_edge-Im_in_edge))

def search_min_z(gamma,Im_in,Im_ref,edge):
    Im_in_=rotate(Im_in,gamma,axes=(1,2),reshape=False)
    Im_in_edge=make_edges(Im_in_)
    Im_in_ref_edge=make_edges(Im_ref)
#    print np.sum((Im_ref-Im_in_)*(Im_ref-Im_in_))
    return np.sum((100-edge)*(Im_ref-Im_in_)*(Im_ref-Im_in_)
                  +edge*(Im_in_ref_edge-Im_in_edge)*(Im_in_ref_edge-Im_in_edge))

def rad(deg):
    return np.pi*deg/180

def make_edges(Im3D_in):
    dz=sp.ndimage.sobel(Im3D_in,0)
    dy=sp.ndimage.sobel(Im3D_in,1)
    dx=sp.ndimage.sobel(Im3D_in,2)
    Im3D=np.hypot(dz,dy,dx)
    Im3D*=255.0/np.max(Im3D)
    return(Im3D)

# MAIN

# This is for another approach using the affine matrix (keeping in for now, possible option later on)
# Use scipy.ndimage.interpolation.affine_transform function
#Rx = [[1,0,0,0],[0,np.cos(rad(alpha)),np.sin(rad(alpha)),0],[0,-np.sin(rad(alpha)),np.cos(rad(alpha)),0],[0,0,0,1]]
#Ry = [[np.cos(rad(beta)),0,-np.sin(rad(beta)),0],[0,1,0,0],[np.sin(rad(beta)),0,np.cos(rad(beta)),0],[0,0,0,1]]
#Rz = [[np.cos(rad(gamma)),np.sin(rad(gamma)),0,0],[-np.sin(rad(gamma)),np.cos(rad(gamma)),0,0],[0,0,1,0],[0,0,0,1]]
#T  = [[1,0,0,Tx],[0,1,0,Ty],[0,0,1,Tz],[0,0,0,1]]

# loading data set
def image_registration(Im4D,ref=1,ref_av=False,min_method='L-BFGS-B',tolerance=0.001,max_iter=100,edge=0,scan2D=1):

    start_time = time.time()

    dyns = np.size(Im4D,0)
    Im4D_out = np.zeros(np.shape(Im4D))
    fits=np.zeros((dyns,6))

    Tx=0.1
    Ty=0.1
    Tz=0.1
    alpha=1.
    beta=1.
    gamma=1.
    
    if ref_av==True:
        Im_ref = Im4D.mean(0)
    else:
        Im_ref = Im4D[ref-1,:,:,:]

    for dyn in range(dyns):
        start_loop=time.time()
        start_fit=time.time()
        result = minimize(search_min_Tx,Tx,args=(Im4D[dyn,:,:,:],Im_ref,edge),tol=tolerance,method=min_method,options={'maxiter':max_iter},
                         bounds=[(-round(0.2*np.size(Im4D,2)),round(0.2*np.size(Im4D,2)))])
        Tx = result.x
        Im4D_out[dyn,:,:,:] = shift(Im4D[dyn,:,:,:],[Tx,0,0])
        print("Tx fit took %s seconds" %int(time.time()-start_fit))

        start_fit=time.time()
        result = minimize(search_min_Ty,Ty,args=(Im4D_out[dyn,:,:,:],Im_ref,edge),tol=tolerance,method=min_method,options={'maxiter':max_iter},
                         bounds=[(-round(0.2*np.size(Im4D,3)),round(0.2*np.size(Im4D,3)))])
        Ty = result.x
        Im4D_out[dyn,:,:,:] = shift(Im4D_out[dyn,:,:,:],[0,Ty,0])
        print("Ty fit took %s seconds" %int(time.time()-start_fit))

        start_fit=time.time()
        result = minimize(search_min_Tz,Tz,args=(Im4D_out[dyn,:,:,:],Im_ref,edge),tol=tolerance,method=min_method,options={'maxiter':max_iter},
                         bounds=[(-round(0.2*np.size(Im4D,1)),round(0.2*np.size(Im4D,1)))])
        if scan2D==1:
            Tz = result.x
            Im4D_out[dyn,:,:,:] = shift(Im4D_out[dyn,:,:,:],[0,0,Tz])
            print("Tz fit took %s seconds" %int(time.time()-start_fit))

            start_fit=time.time()
            result = minimize(search_min_z,gamma,args=(Im4D_out[dyn,:,:,:],Im_ref,edge),tol=tolerance,method=min_method,
                              bounds=[(-45,45)],options={'maxiter':max_iter})
            gamma = result.x
            Im4D_out[dyn,:,:,:] = rotate(Im4D_out[dyn,:,:,:],gamma,axes=(1,2),reshape=False)
            print("gamma fit took %s seconds" %int(time.time()-start_fit))

            start_fit=time.time()
            result = minimize(search_min_y,beta,args=(Im4D_out[dyn,:,:,:],Im_ref,edge),tol=tolerance,method=min_method,
                              bounds=[(-45,45)],options={'maxiter':max_iter})
        beta = result.x
        Im4D_out[dyn,:,:,:] = rotate(Im4D_out[dyn,:,:,:],beta,axes=(0,2),reshape=False)
        print("beta fit took %s seconds" %int(time.time()-start_fit))

        start_fit=time.time()
        result = minimize(search_min_x,alpha,args=(Im4D_out[dyn,:,:,:],Im_ref,edge),tol=tolerance,method=min_method,
                          bounds=[(-45,45)],options={'maxiter':max_iter})
        alpha = result.x
        Im4D_out[dyn,:,:,:] = rotate(Im4D_out[dyn,:,:,:],alpha,axes=(0,1),reshape=False)
        print("alpha fit took %s seconds" %int(time.time()-start_fit))

        fits[dyn,:]=[Tx[0],Ty[0],Tz[0],alpha[0],beta[0],gamma[0]]

        start_fit=time.time()
##        try:
        result = minimize(search_min,fits[dyn,:],args=(Im4D_out[dyn,:,:,:],Im_ref,edge),tol=tolerance*0.1,method=min_method,options={'maxiter':10*max_iter},
                      bounds=[(fits[dyn,0]-0.2*abs(fits[dyn,0]),fits[dyn,0]+0.2*abs(fits[dyn,0])),
                              (fits[dyn,1]-0.2*abs(fits[dyn,1]),fits[dyn,1]+0.2*abs(fits[dyn,1])),
                              (fits[dyn,2]-0.2*abs(fits[dyn,2]),fits[dyn,2]+0.2*abs(fits[dyn,2])),
                              (fits[dyn,3]-0.2*abs(fits[dyn,3]),fits[dyn,3]+0.2*abs(fits[dyn,3])),
                              (fits[dyn,4]-0.2*abs(fits[dyn,4]),fits[dyn,4]+0.2*abs(fits[dyn,4])),
                              (fits[dyn,5]-0.2*abs(fits[dyn,5]),fits[dyn,5]+0.2*abs(fits[dyn,5]))])
##        except TypeError:
##            result = minimize(search_min,fits[dyn,:],args=(Im4D_out[dyn,:,:,:],Im_ref),tol=tolerance*0.1,options={'maxiter':10*max_iter},
##                      bounds=[(fits[dyn,0]-0.2*fits[dyn,0],fits[dyn,0]+0.2*fits[dyn,0]),
##                              (fits[dyn,1]-0.2*fits[dyn,1],fits[dyn,1]+0.2*fits[dyn,1]),
##                              (fits[dyn,2]-0.2*fits[dyn,2],fits[dyn,2]+0.2*fits[dyn,2]),
##                              (fits[dyn,3]-0.2*fits[dyn,3],fits[dyn,3]+0.2*fits[dyn,3]),
##                              (fits[dyn,4]-0.2*fits[dyn,4],fits[dyn,4]+0.2*fits[dyn,4]),
##                              (fits[dyn,5]-0.2*fits[dyn,5],fits[dyn,5]+0.2*fits[dyn,5])])
            
        print("all-in-one fit took %s seconds" %int(time.time()-start_fit))

        fits[dyn,:] = result.x
        print fits[dyn,:]

        Im4D_out[dyn,:,:,:]=rotate(Im4D[dyn,:,:,:],fits[dyn,3],axes=(0,1), reshape=False)
        Im4D_out[dyn,:,:,:]=rotate(Im4D_out[dyn,:,:,:],fits[dyn,4],axes=(0,2), reshape=False)
        Im4D_out[dyn,:,:,:]=rotate(Im4D_out[dyn,:,:,:],fits[dyn,5],axes=(1,2), reshape=False)
        Im4D_out[dyn,:,:,:]=shift(Im4D_out[dyn,:,:,:],[fits[dyn,0],fits[dyn,1],fits[dyn,2]])
    
        run_time = time.time()-start_loop
        if run_time>=60:
            print("fitting time for dynamic %s is %s minutes and %s seconds" %(dyn+1,int(run_time/60),int(run_time-int(run_time/60)*60)) )
        else:
            print("fitting time for dynamic %s is %s seconds" %(dyn+1,int(run_time)))

    run_time = time.time()-start_time
    if run_time>=60:
        print("fitting time for all dynamics is %s minutes and %s seconds" %(int(run_time/60),int(run_time-int(run_time/60)*60)) )
    else:
        print("fitting time for all dynamics is %s seconds" %(int(run_time)))

    return Im4D_out,fits
