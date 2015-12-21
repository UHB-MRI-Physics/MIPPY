from PIL import Image,ImageTk
import dicom
import numpy as np

########################################
########################################
"""
GENERIC FUNCTIONS NOT ATTACHED TO CLASSES
"""
def generate_px_float(pixels,rs,ri,ss):
	return (pixels*rs+ri)/(rs*ss)
	
def get_global_min_and_max(image_list):
	"""
	Will only work with MIPPY_8bitviewer type objects
	"""
	min = np.amin(image_list[0].px_float)
	max = np.amax(image_list[0].px_float)
	for image in image_list:
		if np.amin(image.px_float) < min:
			min = np.amin(image.px_float)
		if np.amax(image.px_float) > max:
			max = np.amax(image.px_float)
	return min,max

########################################
########################################

class MIPPY_8bitviewer():
	"""
	This class wraps up Image.Image and ImageTk.PhotoImage classes so that they can be
	easily rescaled with whatever window and level for display purposes.  It's only 8-bit so
	you don't have the biggest dynamic range, but I'm sure I've heard that the eye can't
	resolve more than 256 shades of grey anyway...
	
	The actual floating point values are stored as an attribute "px_float", so that the actual
	scaled values can also be called for any given x,y position.  This should help when
	constructing an actual viewer.
	"""
	
	def __init__(self,dicom_dataset):
		if type(dicom_dataset) is str or type(dicom_dataset) is unicode:
			ds = dicom.read_file(dicom_dataset)
		elif type(dicom_dataset) is dicom.dataset.FileDataset:
			ds = dicom_dataset
		else:
			print "ERROR GENERATING IMAGE: Constructor input type not understood"
			return
		bitdepth = int(ds.BitsStored)
		pixels = ds.pixel_array.astype(np.float64)
		# DO NOT KNOW IF PIXEL ARRAY ALREADY HANDLES RS AND RI
		try:
			rs = ds[0x28,0x1053].value
		except:
			rs = 1
		try:
			ri = ds[0x28,0x1052].value
		except:
			ri = 0
		try:
			ss = ds[0x2005,0x100E].value
		except:
			ss = 1
		self.px_float = generate_px_float(pixels, rs, ri, ss)
		self.rangemax = generate_px_float(np.power(2,bitdepth), rs, ri, ss)
		self.rangemin = generate_px_float(0,rs,ri,ss)
		self.xscale = ds.PixelSpacing[0]
		self.yscale = ds.PixelSpacing[1]
		#~ self.px_8bit = np.power(2,8)*(((self.px_float)-np.amin(self.px_float))/(np.amax(self.px_float-np.amin(self.px_float))))
		#~ self.px_view = self.px_8bit
		#~ self.image = Image.fromarray(self.px_view)
		#~ self.photoimage = ImageTk.PhotoImage(image)
		self.image = None
		self.photoimage = None
		self.wl_control()
		return

	def wl_control(self,window=None,level=None):
		if window and level:
			self.window = window
			self.level = level
		else:
			self.window = self.rangemax-self.rangemin
			self.level = (self.rangemax-self.rangemin)/2+self.rangemin
		if self.image:
			size=self.image.size
		else:
			size=reversed(np.shape(self.px_float))
		
		if self.level-self.rangemin<self.window/2:
			self.window=2*(self.level-self.rangemin)
		#~ elif self.rangemax-self.level<self.window/2:
			#~ self.window = 2*(self.rangemax-self.level)
		
		windowed_px = np.clip(self.px_float,self.level-self.window/2,self.level+self.window/2-1)
		px_view = np.clip(((windowed_px-np.amin(windowed_px))/self.window * np.power(2,8)),0.,255.).astype(np.uint8)
		self.image = Image.fromarray(px_view, mode='L')
		if not size==self.image.size:
			self.image = self.image.resize(size,Image.ANTIALIAS)
		self.photoimage = ImageTk.PhotoImage(self.image)
		return
		
	def resize(self,dim1=256,dim2=256):
		self.image = self.image.resize((dim1,dim2), Image.ANTIALIAS)
		self.photoimage = ImageTk.PhotoImage(self.image)
		return

