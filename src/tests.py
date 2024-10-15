from io import StringIO
from unittest.mock import patch
from pathlib import Path
from zipfile import Path as ZipPath
from shutil import make_archive

from ShellEmulator import ShellEmulator, CONFIG_PATH, ZIPFILE_PATH, SOURCE_DIR, main

def prepare_test_zip():
    make_archive(ZIPFILE_PATH, 'zip', SOURCE_DIR)

def test_resolve_path():
    prepare_test_zip()
    shell = ShellEmulator(CONFIG_PATH)
    resolved = shell.resolve_path(Path('folder_1'))
    expected = ZipPath(shell.zipfile) / 'folder_1'
    assert resolved == expected

@patch('sys.stdout', new_callable=StringIO)
def test_ls(mock_stdout):
    prepare_test_zip()
    shell = ShellEmulator(CONFIG_PATH)
    shell.ls()
    output = mock_stdout.getvalue()
    assert output == 'folder_1 file1.txt \n'

def test_cd():
    prepare_test_zip()
    shell = ShellEmulator(CONFIG_PATH)
    shell.cd(shell.resolve_path(Path('folder_1')))
    assert shell.format_path(shell.pwd) == 'folder_1/'

@patch('sys.stdout', new_callable=StringIO)
def test_rmdir(mock_stdout):
    prepare_test_zip()
    shell = ShellEmulator(CONFIG_PATH)
    shell.rmdir(shell.resolve_path(Path('folder_1')))
    output = mock_stdout.getvalue()
    assert output == 'Directory not empty: aborting\n'
    shell.rmdir(shell.resolve_path(Path('folder_1/folder_2')))
    shell.cd(shell.resolve_path(Path('folder_1')))
    for file in shell.pwd.iterdir():
        assert file.name != 'folder_2/'

@patch('sys.stdout', new_callable=StringIO)
def test_chown(mock_stdout):
    prepare_test_zip()
    shell = ShellEmulator(CONFIG_PATH)
    shell.chown('file1.txt', 'newuser', 'newgroup')
    assert shell.owners["file1.txt"] == ('newuser', 'newgroup')

@patch('builtins.input', side_effect=['ls', 'exit'])
@patch('sys.stdout', new_callable=StringIO)
def test_io_ls_1(mock_stdout, mock_input):
    main()
    output = mock_stdout.getvalue()
    assert output == 'folder_1 file1.txt \n'

@patch('builtins.input', side_effect=['ls folder_1', 'exit'])
@patch('sys.stdout', new_callable=StringIO)
def test_io_ls_2(mock_stdout, mock_input):
    main()
    output = mock_stdout.getvalue()
    assert output == 'folder_2 file2.txt \n'

@patch('builtins.input', side_effect=['cd folder_1', 'ls', 'exit'])
@patch('sys.stdout', new_callable=StringIO)
def test_io_cd_1(mock_stdout, mock_input):
    main()
    output = mock_stdout.getvalue()
    assert output == 'folder_2 file2.txt \n'

@patch('builtins.input', side_effect=['cd folder_1/..', 'ls', 'exit'])
@patch('sys.stdout', new_callable=StringIO)
def test_io_cd_2(mock_stdout, mock_input):
    main()
    output = mock_stdout.getvalue()
    assert output == 'folder_1 file1.txt \n'

@patch('builtins.input', side_effect=['rmdir folder_1', 'exit'])
@patch('sys.stdout', new_callable=StringIO)
def test_io_rmdir_1(mock_stdout, mock_input):
    main()
    output = mock_stdout.getvalue()
    assert output == 'Directory not empty: aborting\n'

@patch('builtins.input', side_effect=['rmdir folder_1/folder_2', 'ls folder_1', 'exit'])
@patch('sys.stdout', new_callable=StringIO)
def test_io_rmdir_2(mock_stdout, mock_input):
    main()
    output = mock_stdout.getvalue()
    assert output == 'file2.txt \n'

@patch('builtins.input', side_effect=['chown test:test folder_1', 'ls -l', 'exit'])
@patch('sys.stdout', new_callable=StringIO)
def test_io_chown_1(mock_stdout, mock_input):
    main()
    output = mock_stdout.getvalue()
    assert output == 'drwxr-xr-x\t0\ttest\ttest\t(2024, 10, 15, 16, 48, 12)\tfolder_1\n-rw-r--r--\t16\ttestuser\ttestuser_group\t(2024, 10, 15, 13, 2, 12)\tfile1.txt\n'

@patch('builtins.input', side_effect=['chown test:test folder_1/../file1.txt', 'ls -l', 'exit'])
@patch('sys.stdout', new_callable=StringIO)
def test_io_chown_2(mock_stdout, mock_input):
    main()
    output = mock_stdout.getvalue()
    assert output == 'drwxr-xr-x\t0\ttestuser\ttestuser_group\t(2024, 10, 15, 16, 48, 12)\tfolder_1\n-rw-r--r--\t16\ttest\ttest\t(2024, 10, 15, 13, 2, 12)\tfile1.txt\n'

@patch('builtins.input', side_effect=['cal 2024', 'exit'])
@patch('sys.stdout', new_callable=StringIO)
def test_io_cal_1(mock_stdout, mock_input):
    main()
    output = mock_stdout.getvalue()
    assert output == '                                  2024\n\n      January                   February                   March\nMo Tu We Th Fr Sa Su      Mo Tu We Th Fr Sa Su      Mo Tu We Th Fr Sa Su\n 1  2  3  4  5  6  7                1  2  3  4                   1  2  3\n 8  9 10 11 12 13 14       5  6  7  8  9 10 11       4  5  6  7  8  9 10\n15 16 17 18 19 20 21      12 13 14 15 16 17 18      11 12 13 14 15 16 17\n22 23 24 25 26 27 28      19 20 21 22 23 24 25      18 19 20 21 22 23 24\n29 30 31                  26 27 28 29               25 26 27 28 29 30 31\n\n       April                      May                       June\nMo Tu We Th Fr Sa Su      Mo Tu We Th Fr Sa Su      Mo Tu We Th Fr Sa Su\n 1  2  3  4  5  6  7             1  2  3  4  5                      1  2\n 8  9 10 11 12 13 14       6  7  8  9 10 11 12       3  4  5  6  7  8  9\n15 16 17 18 19 20 21      13 14 15 16 17 18 19      10 11 12 13 14 15 16\n22 23 24 25 26 27 28      20 21 22 23 24 25 26      17 18 19 20 21 22 23\n29 30                     27 28 29 30 31            24 25 26 27 28 29 30\n\n        July                     August                  September\nMo Tu We Th Fr Sa Su      Mo Tu We Th Fr Sa Su      Mo Tu We Th Fr Sa Su\n 1  2  3  4  5  6  7                1  2  3  4                         1\n 8  9 10 11 12 13 14       5  6  7  8  9 10 11       2  3  4  5  6  7  8\n15 16 17 18 19 20 21      12 13 14 15 16 17 18       9 10 11 12 13 14 15\n22 23 24 25 26 27 28      19 20 21 22 23 24 25      16 17 18 19 20 21 22\n29 30 31                  26 27 28 29 30 31         23 24 25 26 27 28 29\n                                                    30\n\n      October                   November                  December\nMo Tu We Th Fr Sa Su      Mo Tu We Th Fr Sa Su      Mo Tu We Th Fr Sa Su\n    1  2  3  4  5  6                   1  2  3                         1\n 7  8  9 10 11 12 13       4  5  6  7  8  9 10       2  3  4  5  6  7  8\n14 15 16 17 18 19 20      11 12 13 14 15 16 17       9 10 11 12 13 14 15\n21 22 23 24 25 26 27      18 19 20 21 22 23 24      16 17 18 19 20 21 22\n28 29 30 31               25 26 27 28 29 30         23 24 25 26 27 28 29\n                                                    30 31\n\n'

@patch('builtins.input', side_effect=['cal 2023', 'exit'])
@patch('sys.stdout', new_callable=StringIO)
def test_io_cal_2(mock_stdout, mock_input):
    main()
    output = mock_stdout.getvalue()
    assert output == '                                  2023\n\n      January                   February                   March\nMo Tu We Th Fr Sa Su      Mo Tu We Th Fr Sa Su      Mo Tu We Th Fr Sa Su\n                   1             1  2  3  4  5             1  2  3  4  5\n 2  3  4  5  6  7  8       6  7  8  9 10 11 12       6  7  8  9 10 11 12\n 9 10 11 12 13 14 15      13 14 15 16 17 18 19      13 14 15 16 17 18 19\n16 17 18 19 20 21 22      20 21 22 23 24 25 26      20 21 22 23 24 25 26\n23 24 25 26 27 28 29      27 28                     27 28 29 30 31\n30 31\n\n       April                      May                       June\nMo Tu We Th Fr Sa Su      Mo Tu We Th Fr Sa Su      Mo Tu We Th Fr Sa Su\n                1  2       1  2  3  4  5  6  7                1  2  3  4\n 3  4  5  6  7  8  9       8  9 10 11 12 13 14       5  6  7  8  9 10 11\n10 11 12 13 14 15 16      15 16 17 18 19 20 21      12 13 14 15 16 17 18\n17 18 19 20 21 22 23      22 23 24 25 26 27 28      19 20 21 22 23 24 25\n24 25 26 27 28 29 30      29 30 31                  26 27 28 29 30\n\n        July                     August                  September\nMo Tu We Th Fr Sa Su      Mo Tu We Th Fr Sa Su      Mo Tu We Th Fr Sa Su\n                1  2          1  2  3  4  5  6                   1  2  3\n 3  4  5  6  7  8  9       7  8  9 10 11 12 13       4  5  6  7  8  9 10\n10 11 12 13 14 15 16      14 15 16 17 18 19 20      11 12 13 14 15 16 17\n17 18 19 20 21 22 23      21 22 23 24 25 26 27      18 19 20 21 22 23 24\n24 25 26 27 28 29 30      28 29 30 31               25 26 27 28 29 30\n31\n\n      October                   November                  December\nMo Tu We Th Fr Sa Su      Mo Tu We Th Fr Sa Su      Mo Tu We Th Fr Sa Su\n                   1             1  2  3  4  5                   1  2  3\n 2  3  4  5  6  7  8       6  7  8  9 10 11 12       4  5  6  7  8  9 10\n 9 10 11 12 13 14 15      13 14 15 16 17 18 19      11 12 13 14 15 16 17\n16 17 18 19 20 21 22      20 21 22 23 24 25 26      18 19 20 21 22 23 24\n23 24 25 26 27 28 29      27 28 29 30               25 26 27 28 29 30 31\n30 31\n\n'