# Generic functions for MIPPY windows that don't fit anywhere else

def optionmenu_patch(om, var):
    menu = om['menu']
    last = menu.index("end")
    for i in range(0, last+1):
        menu.entryconfig(i, variable=var)