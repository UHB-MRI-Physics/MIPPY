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

def find_phantom_center(image,phantom='ACR',subpixel=True,mode='valid'):
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