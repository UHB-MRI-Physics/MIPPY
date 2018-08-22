from mippy.fileio import *

def test_list_all_files():
	dir = 'test_data/dirsearch'
	files_shallow = list_all_files('test_data/DirSearch')
	files_deep = list_all_files('test_data',recursive=True)
	assert len(files_shallow)==2
	assert len(files_deep)==5

def test_save_results():
	pass

def test_export_dicom_file():
	pass

def test_remove_invalid_characters():
	test_str_1 = r'a\b/c:d*e?f"g<h>i|j'
	test_str_2 = 'a\\b/c:d*e?f"g<h>i|j'
	assert remove_invalid_characters(test_str_1) == 'abcdefghij'
	assert remove_invalid_characters(test_str_2) == 'abcdefghij'