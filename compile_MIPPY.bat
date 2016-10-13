@echo off
cd ..
python .\MIPPY\compile_pyc.py .\MIPPY
M:\Software_Programs\Python27\Scripts\pyinstaller ^
	-D ^
	-i .\MIPPY\source\images\brain_orange.ico ^
	--hidden-import=FixTk ^
	--hidden-import=scipy.linalg ^
	--hidden-import=scipy.linalg.cython_blas ^
	--hidden-import=scipy.linalg.cython_lapack ^
	--hidden-import=source.functions ^
	--hidden-import=modules ^
	--win-no-prefer-redirects ^
	--win-private-assemblies ^
	--hidden-import=easygui ^
	.\MIPPY\MIPPY.pyw

mkdir .\dist\MIPPY\logs
mkdir .\dist\MIPPY\modules
mkdir .\dist\MIPPY\source
mkdir .\dist\MIPPY\source\images
mkdir .\dist\MIPPY\source\functions

xcopy .\MIPPY\source\images\* .\dist\MIPPY\source\images /E
xcopy .\MIPPY\modules\*.pyc .\dist\MIPPY\modules /E
xcopy .\MIPPY\source\functions\*.pyc .\dist\MIPPY\source\functions /E
xcopy .\MIPPY\modules\*config .\dist\MIPPY\modules /E
xcopy .\MIPPY\FixTk.pyc .\dist\MIPPY