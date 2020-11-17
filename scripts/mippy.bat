@echo off
cd %~1
py -3.7 -c "from mippy.launcher import *;launch_mippy()"
