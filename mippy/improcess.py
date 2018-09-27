import numpy as np
from scipy.signal import convolve2d
from scipy.ndimage.measurements import center_of_mass
from scipy.optimize import minimize
from scipy.ndimage import convolve, gaussian_filter


def find_object_geometry_edges(image,subpixel=True):
        edges = edge_detect_2d(image.px_float)
        xmin,xmax,ymin,ymax,xc,yc = get_bounding_box(edges)
        return xc,yc,(xmax-xmin)/2,(ymax-ymin)/2

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
                        try:
                                xsol = int(np.round(np.sqrt((1.-(((y-yc+1)**2)/(yr**2)))*(xr**2)),0))
                        except ValueError:
                                # Square root of negative, probably means this is right on the boundary??  Will only
                                # be negative due to inaccuracies of computer maths/floating points.  e.g. -10^-12 instead
                                # of zero.  Assume xsol is zero and move on
                                xsol = 0
                        except:
                                print(y,yc,yr,xr,(1.-(((y-yc+1)**2)/(yr**2)))*(xr**2))
                                raise
                        #~ print y, xsol
                y = int(np.round(y,0))
                xc = int(np.round(xc,0))
                mask[y,xc-xsol:xc+xsol+1]=1.
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

def edge_detect_2d(im,blur=5,highThreshold=91,lowThreshold=31,ignore_edges=8):
        """
        Implementation of a canny edge fiter.
        Input a numpy array of pixel values for an image, get an array of
        pixel values back for the edge-filtered image.
        Based on rosettacode.org/wiki/Canny_edge_detector#Python
        """
        
        if ignore_edges>0:
                im[0:ignore_edges,:]=0
                im[-ignore_edges:0,:]=0
                im[:,0:ignore_edges]=0
                im[:,-ignore_edges:0]=0
        
        # Gaussian blur to remove noise
        im2 = gaussian_filter(im,blur)
        
        # Use sobel filters to get horizontal and vertical gradients
        im3h = convolve(im2,[[-1,0,1],[-2,0,2],[-1,0,1]])
        im3v = convolve(im2,[[1,2,1],[0,0,0],[-1,-2,-1]])
        
        #Get gradient and direction
        grad = np.power(np.power(im3h, 2.0) + np.power(im3v, 2.0), 0.5)
        theta = np.arctan2(im3v, im3h)
        thetaQ = (np.round(theta * (5.0 / np.pi)) + 5) % 5 #Quantize direction
        
        #Non-maximum suppression
        gradSup = grad.copy()
        for r in range(im.shape[0]):
                for c in range(im.shape[1]):
                        #Suppress pixels at the image edge
                        if r == 0 or r == im.shape[0]-1 or c == 0 or c == im.shape[1] - 1:
                                gradSup[r, c] = 0
                                continue
                        tq = thetaQ[r, c] % 4
 
                        if tq == 0: #0 is E-W (horizontal)
                                if grad[r, c] <= grad[r, c-1] or grad[r, c] <= grad[r, c+1]:
                                        gradSup[r, c] = 0
                        if tq == 1: #1 is NE-SW
                                if grad[r, c] <= grad[r-1, c+1] or grad[r, c] <= grad[r+1, c-1]:
                                        gradSup[r, c] = 0
                        if tq == 2: #2 is N-S (vertical)
                                if grad[r, c] <= grad[r-1, c] or grad[r, c] <= grad[r+1, c]:
                                        gradSup[r, c] = 0
                        if tq == 3: #3 is NW-SE
                                if grad[r, c] <= grad[r-1, c-1] or grad[r, c] <= grad[r+1, c+1]:
                                        gradSup[r, c] = 0
 
        #Double threshold
        strongEdges = (gradSup > highThreshold)
 
        #Strong has value 2, weak has value 1
        thresholdedEdges = np.array(strongEdges, dtype=np.uint8) + (gradSup > lowThreshold)
 
        #Tracing edges with hysteresis	
        #Find weak edge pixels near strong edge pixels
        finalEdges = strongEdges.copy()
        currentPixels = []
        for r in range(1, im.shape[0]-1):
                for c in range(1, im.shape[1]-1):	
                        if thresholdedEdges[r, c] != 1:
                                continue #Not a weak pixel
 
                        #Get 3x3 patch	
                        localPatch = thresholdedEdges[r-1:r+2,c-1:c+2]
                        patchMax = localPatch.max()
                        if patchMax == 2:
                                currentPixels.append((r, c))
                                finalEdges[r, c] = 1
 
        #Extend strong edges based on current pixels
        while len(currentPixels) > 0:
                newPix = []
                for r, c in currentPixels:
                        for dr in range(-1, 2):
                                for dc in range(-1, 2):
                                        if dr == 0 and dc == 0: continue
                                        r2 = r+dr
                                        c2 = c+dc
                                        if thresholdedEdges[r2, c2] == 1 and finalEdges[r2, c2] == 0:
                                                #Copy this weak pixel to final result
                                                newPix.append((r2, c2))
                                                finalEdges[r2, c2] = 1
                currentPixels = newPix
        finalEdges = finalEdges.astype(np.float32)
        print(np.min(finalEdges),np.max(finalEdges))
        return finalEdges

def get_bounding_box(im):
        """
        Return the bounding box of non-zero image pixels
        """
        rows = np.any(im, axis=1)
        cols = np.any(im, axis=0)
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]

        #~ return rmin, rmax, cmin, cmax, (rmax-rmin)/2+rmin, (cmax-cmin)/2+cmin
        return cmin, cmax, rmin, rmax, (cmax-cmin)/2+cmin, (rmax-rmin)/2+rmin