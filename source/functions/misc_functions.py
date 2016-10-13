# -*- coding: utf-8 -*-
"""
Created on Thu Oct 13 11:58:23 2016

@author: rob

Miscellaneous functions for MIPPY


"""

def optionmenu_patch(om, var):
    menu = om['menu']
    last = menu.index("end")
    for i in range(0, last+1):
        menu.entryconfig(i, variable=var)