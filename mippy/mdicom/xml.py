"""
XML generators and readers for use with pydicom objects.

This is to improve serialisation and (potentially) reduce the file-size
of MIPPY temp files.  Pixel data is dumped separately with numpy.

The file_meta, header and pixel data are stored as 3 separate files
(where [UID] is the SOP instance UID).

[UID]_meta.xml
[UID]_header.xml
[UID]_px.pix
"""