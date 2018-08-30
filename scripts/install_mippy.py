from easygui import diropenbox,choicebox,msgbox
import sys
import os
from subprocess import call
import getpass

user = getpass.getuser()

DEFAULT_DIR = r'C:\MIPPY_'+str(user)

MESSAGE = (
	'This sets up a MIPPY working directory and creates a shortcut\n'
	+'in the Start Menu from which you can launch MIPPY.\n\n'
	+'The working directory is where you should install\n'
	+'your modules for MIPPY.\n\n'
	+'Would you like to use the default directory ('+DEFAULT_DIR+') or\n'
	+'select a different directory?')

choices = ['Default directory ('+DEFAULT_DIR+')','Different direcrtory']

user_choice = choicebox(msg=MESSAGE,title="INSTALL MIPPY",
				choices=choices,
				preselect=0,run=True)

if user_choice==choices[1]:
	install_dir = diropenbox("Select a directory in which to install MIPPY",
						"SELECT INSTALL DIRECTORY",
						DEFAULT_DIR)
elif user_choice==choices[0]:
	install_dir = DEFAULT_DIR
else:
	sys.exit()

#~ print(install_dir)
module_dir = os.path.join(install_dir,'modules')

if not os.path.exists(module_dir):
	os.makedirs(module_dir)
os.environ['MIPPYPATH']='\"'+install_dir+'\"'

start_command = '@echo off\nmippy \"'+install_dir+'\"'
#~ print(start_command)

with open(os.path.join(install_dir,'start_mippy.bat'),'w') as f:
	f.write(start_command)

# Create Start Menu folder:
start_menu_dir=os.path.join(os.environ['userprofile'],'Start Menu','Programs','MIPPY')
if not os.path.exists(start_menu_dir):
	os.makedirs(start_menu_dir)

mippy_link_path = os.path.join(start_menu_dir,'MIPPY.lnk')

if os.path.exists(mippy_link_path):
	os.remove(mippy_link_path)

command=('powershell $s=(New-Object -COM WScript.Shell).CreateShortcut(\''
			+os.path.join(start_menu_dir,'MIPPY.lnk')
			+'\');$s.TargetPath=\''
			+os.path.join(install_dir,'start_mippy.bat')
			+'\';$s.Save()')
#~ print(command)
call(command)



if os.path.exists(mippy_link_path):
	END_MESSAGE = (
		'MIPPY was successfully installed!\n\n'
		+'You can now run MIPPY from the Start Menu, or from\n'
		+'the selected installation directory of:\n\n'
		+install_dir
		)
	end = msgbox(msg=END_MESSAGE,title="Success!")
else:
	END_MESSAGE = (
		'Unable to create shortcut on Start Menu.  Please\n'
		+'seek help.\n\n'
		+'In the meantime, you should still be able to run\n'
		+'MIPPY from your selected installation directory of:\n\n'
		+install_dir
		)
	end = msgbox(msg=END_MESSAGE,title="Oops...")