from distutils.core import setup

setup(	name			=	'MIPPY',
		version		=	'0.4-0',
		description		=	'Modular Image Processing in Python',
		author		=	'Robert Flintham',
		author_email	=	'robert.flintham@uhb.nhs.uk',
		install_requires	=	[
						'numpy',
						'importlib',
						'pydicom',
						'datetime',
						're',
						'csv',
						'pillow'
						]
	)