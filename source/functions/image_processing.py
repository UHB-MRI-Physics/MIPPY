import dicom
import numpy as np
import platform
from scipy.signal import convolve2d
from scipy.ndimage.measurements import center_of_mass
from matplotlib import pyplot as plt
from scipy.optimize import minimize
from time import sleep
from copy import deepcopy
#from source.functions.viewer_functions import *

"""
This module contains only functions for the analysis of 2D or 3D image data
which must be passed MIPPYImage objects.
"""

def find_phantom_center_old(image,phantom='ACR',subpixel=True,mode='valid'):
	"""
	Assumes circular/ellipsoid phantom.  For anything else, you'll
	need a different method.

	IMPORTANT - returns (x,y) as tuple, but arrays work in [row,col]
	i.e. [y,x] when indexing values
	"""

	# Calculate phantom radius in pixels
	if phantom=='ACR (TRA)':
		radius_x = 95./image.xscale
		radius_y = 95./image.yscale
	elif phantom=='ACR (SAG)':
		radius_x = 95./image.xscale
		radius_y = 79./image.yscale
	elif phantom=='ACR (COR)':
		radius_x = 95./image.xscale
		radius_y = 79./image.yscale
	elif phantom=='MagNET Flood (TRA)':
		radius_x = 95./image.xscale
		radius_y = 95./image.yscale
	elif phantom=='MagNET Flood (SAG)':
		radius_x = 95./image.xscale
		radius_y = 105./image.yscale
	elif phantom=='MagNET Flood (COR)':
		radius_x = 95./image.xscale
		radius_y = 105./image.yscale
		# Add other phantom dimensions here...
	else:
		print "ERROR: Phantom not recognised"
		if subpixel:
			return (float(image.columns/2), float(image.rows/2))
		else:
			return (int(image.columns/2), int(image.rows/2))
	mask_size = (int(np.round(radius_y*2+3,0)),int(np.round(radius_x*2+3,0)))
	offset_x = radius_x+1
	offset_y = radius_y+1
	mask = np.zeros(mask_size).astype(np.float64)
	for i in range(np.shape(mask)[0]):
		for j in range(np.shape(mask)[1]):
			x = float(j)
			y = float(i)
			if ((x-offset_x)**2/radius_x**2)+((y-offset_y)**2/radius_y**2)<=1.:
				mask[i,j]=1.
	mask = mask/np.sum(mask)
#	plt.imshow(mask)
#	plt.show()
#	sleep(1)

	# Create binary image
	px = deepcopy(image.px_float)
	threshold = np.mean(px)/5
	px[px<threshold]=0
	px[px>=threshold]=1

	print "made binary"
#	plt.imshow(px)
#	plt.show()
	print "continuing"
	print mode

	if mode=='valid':
		mega_smooth=convolve2d(px,mask,mode='valid')
		mask_offset_y = (mask_size[0]+1)/2
		mask_offset_x = (mask_size[1]+1)/2
	elif mode=='same':
		mega_smooth=convolve2d(px,mask,mode='same')
		mask_offset_y = 0
		mask_offset_x = 0
#	center = center_of_mass(mega_smooth)
#	plt.imshow(mega_smooth)
#	plt.show()
#	sleep(1)

	max_indices = np.where(mega_smooth==mega_smooth.max())
	x_y_coords = zip(max_indices[0],max_indices[1])
	print x_y_coords
	center = x_y_coords[0]
	print center
	x = center[1]+mask_offset_x
	y = center[0]+mask_offset_y
	print x,y
	if subpixel:
		result = minimize(get_inverse_sum,[center[1],center[0]],args=(mega_smooth,20))
		x = result.x[0]+mask_offset_x
		y = result.x[1]+mask_offset_y
	print x,y
	if subpixel:
		return (x,y)
	else:
		return (int(np.round(x,0)),int(np.round(y,0)))

def find_phantom_center(image,phantom='ACR',subpixel=True,mode='valid'):
	geo = find_phantom_geometry(image,subpixel)
	return (geo[0],geo[1])

def phantom_fit_rectangle(geo,px_binary):
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

def phantom_fit_ellipse(geo,px_binary):
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

def find_phantom_geometry(image,subpixel=True):
	"""
	Takes a MIPPY image and finds the best fit of an ellipse or rectangle to the
	object in the image.
	
	Returns the centre, shape type and X/Y radius/half length.
	"""
	px = image.px_float
	shape_px = np.shape(px)
	px_binary = np.zeros(shape_px).astype(np.float64)
	# Make binary
	threshold = 0.05*np.mean(px[np.where(px>np.percentile(px,75))])
	px_binary[np.where(px>threshold)] = 1.
	#~ np.savetxt(r"K:\binarypx.txt",px_binary)
	xc=float(shape_px[1]/2)
	yc=float(shape_px[0]/2)
	xr=float(shape_px[1]/3)
	yr=float(shape_px[0]/3)
	print "Fitting ellipse"
	best_ellipse = minimize(phantom_fit_ellipse,(xc,yc,xr,yr),args=(px_binary),method='Nelder-Mead',options={'maxiter':30})
	#~ best_ellipse = minimize(phantom_fit_ellipse,(xc,yc,xr,yr),args=(px_binary),options={'maxiter':10})
	#~ print best_ellipse.success
	print "Fitting rectangle"
	best_rectangle = minimize(phantom_fit_rectangle,(xc,yc,xr,yr),args=(px_binary),method='Nelder-Mead',options={'maxiter':30})
	#~ best_rectangle = minimize(phantom_fit_rectangle,(xc,yc,xr,yr),args=(px_binary),options={'maxiter':10})
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
		print "Something went wrong"
	
	print result,shapetype
	
	
	# Return xc,yc,xr,yr,shapetype
	return (result[0],result[1],result[2],result[3],shapetype)

def get_inverse_sum(c,arr,size=3):
	# c is center in [x,y] format
	return abs(1/np.sum(arr[c[1]-size:c[1]+size,c[0]-size:c[0]+size]))

class MR_Phantom(object):
	def __init__(self,shape,radius=None,length=None,width=None,height=None):
		if shape=='cylinder' and radius and length:
			self._r = float(radius)
			self._l = float(length)
			self._w = None
			self._h = None
		elif shape=='sphere' and radius:
			self._r = float(radius)
			self._l = None
			self._w = None
			self._h = None
		elif shape=='cuboid' and length and width and height:
			self._r = None
			self._l = float(length)
			self._w = float(width)
			self._h = float(height)
		else:
			print "Failed to initialise phantom"
			raise ShapeError('Phantom shape/measurements not understood.')
		return

class ShapeError(Exception):
	def __init__(self,value):
		self.value = value
	def __str__(self):
		return repr(self.value)

def make_ACR():
	return MR_Phantom('cylinder',radius=95,length=160)

def make_MagNET_flood():
	return MR_Phantom('cylinder',radius=100,length=200)