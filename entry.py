#!python
if __name__=='__main__':
    import sys
    import os
    sys.path.append(os.getcwd())
    from mippy.launcher import *
    if getattr(sys, 'frozen', False):
        FROZEN = True
    else:
        FROZEN = False
    # print(FROZEN)
    if FROZEN:
        launch_mippy()
    else:
        launch_mippy(skip_update=True)
