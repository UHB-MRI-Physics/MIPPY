Useful References
#######################

GUI Design
-------------------

MIPPY is built on **tkinter**, the default GUI package that comes with Python distributions.  There's a bit of a learning curve, but the best resource I have found for getting your head around it (and checking your syntax) is the site at **effbot.org**.

`effbot.org/tkinterbook <http://effbot.org/tkinterbook>`_

*A caveat: This was written for Python2, but MIPPY now only works on Python3.  Nothing much has changed in tkinter, except for the import statements. For more info, see `this answer <https://stackoverflow.com/questions/17843596/difference-between-tkinter-and-tkinter>`_ on StackOverflow.*

Pydicom
--------------------

The second resource you'll probably need is the `documentation for Pydicom <http://pydicom.github.io/pydicom/stable/>`_.  For anything to do with reading/writing DICOM files or working with DICOM header information, this is your best bet.

http://pydicom.github.io/pydicom/stable

Numpy & Scipy
--------------------------
MIPPY relies heavily on numpy and scipy, and if you're working with pixel data then you'll probably also want to do so.  The documentation for these is **excellent**, and is the same format I've tried to use for the API-like parts of the documentation on this site.

Numpy: https://docs.scipy.org/doc/numpy-1.15.1/reference/

Scipy: https://docs.scipy.org/doc/scipy-1.1.0/reference/

Python documentation
---------------------------

Most other stuff MIPPY does uses built-in Python libraries. The Python documentation is very good, so it is definitely a recommended resource.

http://docs.python.org/3/index.html
