#!python
if __name__=='__main__':
    import sys
    import os
    sys.path.append(os.getcwd())
    from mippy.launcher import *
    print(getattr(sys, 'frozen'))
    if getattr(sys, 'frozen', True):
        FROZEN = True
    else:
        FROZEN = False
    print(FROZEN)
    if FROZEN:
        launch_mippy()
    else:
        launch_mippy(skip_update=True)
