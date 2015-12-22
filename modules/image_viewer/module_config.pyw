import cPickle as pickle
from easygui import multenterbox
import os

cfg_file = 'config'

if os.path.exists(cfg_file):
	with open(cfg_file,'r') as file_object:
		module_info = pickle.load(file_object)
	name = module_info['name']
	description = module_info['description']
	author = module_info['author']
else:
	name = ''
	description = ''
	author= ''
	
dirname = os.path.split(os.getcwd())[1]

name,description,author = multenterbox(

	"Please complete the fields below to set up your module.",
	"MIPPY: Module configuration dialog",
	["Module name","Module description","Author"],
	[name,description,author]

)

module_info = {'name':name,'description':description,'author':author,'dirname':dirname}

with open(cfg_file, 'w') as file_object:
	pickle.dump(module_info,file_object)