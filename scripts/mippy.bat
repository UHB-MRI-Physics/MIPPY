@echo off
cd %~1
python -c "from mippy.launcher import *;launch_mippy()"