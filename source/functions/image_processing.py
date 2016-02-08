import dicom
import numpy as np
import platform
from scipy.signal import convolve2d
from scipy.ndimage.measurements import center_of_mass

"""
This module contains only functions for the analysis of 2D or 3D image data
which must be passed MIPPYImage objects.
"""

def find_phantom_center(image,phantom='ACR',subpixel=True):
	"""
	Assumes circular/ellipsoid phantom.  For anything else, you'll
	need a different method.
	
	IMPORTANT - returns (x,y) as tuple, but arrays work in [row,col]
	i.e. [y,x] when indexing values    
	"""
	
	# Calculate phantom radius in pixels
	if phantom=='ACR':
		radius_x = 95./image.xscale
		radius_y = 95./image.yscale
		# Add other phantom dimensions here...
	else:
		print "ERROR: Phantom not recognised"
		if subpixel:
			return (float(image.columns/2), float(image.rows/2))
		else:
			return (int(image.columns/2), int(image.rows/2))
	mask_size = (int(np.round(radius_y*2+3,0)),int(np.round(radius_x*2+3,0)))
	offset_x = radius_x+1
	offset_y = radius_x+1
	mask = np.zeros(mask_size).astype(np.float64)
	for i in range(np.shape(mask)[0]):
		for j in range(np.shape(mask)[1]):
			x = float(j)
			y = float(i)
			if ((x-offset_x)**2/radius_x**2)+((y-offset_y)**2/radius_y**2)<=1.:
				mask[i,j]=1.
	mask = mask/np.sum(mask)
	print mask[90,90]
	
	mega_smooth=convolve2d(image.px_float,mask,mode='valid')
	center = center_of_mass(mega_smooth)
	print center
	x = center[1]+(mask_size[1]+1)/2
	y = center[0]+(mask_size[0]+1)/2
	if subpixel:
		return (x,y)
	else:
		return (int(np.round(x)),int(np.round(y)))