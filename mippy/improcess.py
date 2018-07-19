import numpy as np
from scipy.signal import convolve2d
from scipy.ndimage.measurements import center_of_mass
from scipy.optimize import minimize


def find_object_geometry(image,subpixel=True):
        """
        Takes a MIPPY image and finds the best fit of an ellipse or rectangle to the
        object in the image.
        
        Returns the centre, shape type and X/Y radius/half length.
        """
        px = image.px_float
        shape_px = np.shape(px)
        px_binary = np.zeros(shape_px).astype(np.float64)
        # Make binary
        threshold = 0.1*np.mean(px[np.where(px>np.percentile(px,75))])
        px_binary[np.where(px>threshold)] = 1.
        #~ np.savetxt(r"K:\binarypx.txt",px_binary)
        xc=float(shape_px[1]/2)
        yc=float(shape_px[0]/2)
        xr=float(shape_px[1]/3)
        yr=float(shape_px[0]/3)
        print("Fitting ellipse")
        best_ellipse = minimize(object_fit_ellipse,(xc,yc,xr,yr),args=(px_binary),method='Nelder-Mead',options={'maxiter':30})
        #~ best_ellipse = minimize(object_fit_ellipse,(xc,yc,xr,yr),args=(px_binary),options={'maxiter':10})
        #~ print best_ellipse.success
        print("Fitting rectangle")
        best_rectangle = minimize(object_fit_rectangle,(xc,yc,xr,yr),args=(px_binary),method='Nelder-Mead',options={'maxiter':30})
        #~ best_rectangle = minimize(object_fit_rectangle,(xc,yc,xr,yr),args=(px_binary),options={'maxiter':10})
        #~ print best_rectangle.success
        
        ellipse_val = best_ellipse.fun
        rectangle_val = best_rectangle.fun
        
        #~ print ellipse_val
        #~ print rectangle_val
        
        if ellipse_val < rectangle_val:
                result = best_ellipse.x
                shapetype='ellipse'
        elif ellipse_val > rectangle_val:
                result = best_rectangle.x
                shapetype='rectangle'
        else:
                print("Something went wrong")
        
        print(result,shapetype)
        
        
        # Return xc,yc,xr,yr,shapetype
        if subpixel:
                return (result[0],result[1],result[2],result[3],shapetype)
        else:
                result[0] = int(np.round(result[0],0))
                result[1] = int(np.round(result[1],0))
                result[2] = int(np.round(result[2],0))
                result[3] = int(np.round(result[3],0))
                return (result[0],result[1],result[2],result[3],shapetype)

def object_fit_ellipse(geo,px_binary):
        """
        geo is a tuple in the format xc,yc,xr,yr)
        """
        shape_px = np.shape(px_binary)
        mask = np.zeros(shape_px).astype(np.float64)
        xc=geo[0]
        yc=geo[1]
        xr=geo[2]
        yr=geo[3]
        #~ if xr>xc:
                #~ xmin=0
        #~ else:
                #~ xmin=int(xc-xr)
        #~ if xc+xr>shape_px[1]:
                #~ xmax=shape_px[1]
        #~ else:
                #~ xmax=int(xc+xr)
        if yr>yc:
                ymin=0
        else:
                ymin=int(yc-yr-1)
        if yc+yr>shape_px[0]:
                ymax=shape_px[0]
        else:
                ymax=int(yc+yr)
        #~ print "making mask"
        for y in range(ymin,ymax):
                y = float(y)
                if ((y-yc)**2)>(yr**2):
                        #~ print y, "Skipping"
                        continue
                else:
                        xsol = int(np.round(np.sqrt((1.-(((y-yc+1)**2)/(yr**2)))*(xr**2)),0))
                        #~ print y, xsol
                y = int(np.round(y,0))
                xc = int(np.round(xc,0))
                mask[y,xc-xsol+1:xc+xsol+1]=1.
                #~ for x in range(xmin,xmax):
                        #~ x = float(x)
                        #~ y = float(y)
                        #~ if abs(x-xc)**2/xr**2 + abs(y-yc)**2/yr**2 <= 1.:
                                #~ mask[y,x]=1.
        #~ print "done making mask"
        #~ np.savetxt(r'K:\binarymaskellipse.txt',mask)
        result = np.sum(np.abs(mask-px_binary))
        #~ print float(result)/100000
        return float(result)/100000

def object_fit_rectangle(geo,px_binary):
        """
        geo is a tuple in the format xc,yc,xr,yr)
        """
        shape_px = np.shape(px_binary)
        mask = np.zeros(shape_px).astype(np.float64)
        xc=geo[0]
        yc=geo[1]
        xr=geo[2]
        yr=geo[3]
        if xr>xc:
                xmin=0
        else:
                xmin=int(xc-xr)
        if xc+xr>shape_px[1]:
                xmax=shape_px[1]
        else:
                xmax=int(xc+xr)
        if yr>yc:
                ymin=0
        else:
                ymin=int(yc-yr)
        if yc+yr>shape_px[0]:
                ymax=shape_px[0]
        else:
                ymax=int(yc+yr)
        #~ print "making mask"
        mask[ymin:ymax,xmin:xmax]=1.
        #~ np.savetxt(r'K:\binarymaskrectangle.txt',mask)
        result = np.sum(np.abs(mask-px_binary))
        #~ print float(result)/100000
        return float(result)/100000

def get_inverse_sum(c,arr,size=3):
        # c is center in [x,y] format
        return abs(1/np.sum(arr[c[1]-size:c[1]+size,c[0]-size:c[0]+size]))