import numpy as np
from scipy.optimize import minimize
from scipy.ndimage.interpolation import rotate
from scipy.ndimage.interpolation import shift
from sklearn.metrics import mutual_info_score
from viewer_functions import *


# matrix must be of the form [Tx,Ty,Tz,Rx,Ry,Rz]

def transform(Image,matrix):
	shifted_image = shift(Image,matrix[0:3],output=np.float64)
	z_rotated_image = rotate(shifted_image,matrix[5],axes=(2,1),reshape=False,output=np.float64)
	y_rotated_image = rotate(z_rotated_image,matrix[4],axes=(2,0),reshape=False,output=np.float64)
	x_rotated_image = rotate(y_rotated_image,matrix[3],axes=(1,0),reshape=False,output=np.float64)
	return x_rotated_image

def get_MI(Image1,Image2):
	#flatIm1 = Image1[:][:][::10].flatten()
	#flatIm2 = Image2[:][:][::10].flatten()
	#MI = mutual_info_score(flatIm1,flatIm2)
	MI = (np.sum((Image1-Image2))**2)
	return MI

def registration_function(matrix,Image1,Image2):
	new_Im2 = transform(Image2,matrix)
	return get_MI(Im1,new_Im2)



Im1 = np.array(range(10000)).astype(np.float64).reshape((1,100,100))
Im2 = transform(Im1,[0,20,15,0,0,25])

result = minimize(registration_function,[0,-5,-5,0,0,-10],args=(Im1,Im2),tol=0.000001,options={'maxiter':50})
print result.x

registered_Im2 = transform(Im2,result.x)

#quick_display(Im1[0])
quick_display(registered_Im2[0])