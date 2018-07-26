@echo off
FOR /R deps %%F in (numpy*) do python -m pip install %%F & ^
FOR /R deps %%F in (scipy*) do python -m pip install %%F & ^
FOR /R current %%F in (MIPPY*) do python -m pip install %%F & ^

pause