import zipfile
import shutil
import stat
import csv
import xml.etree.ElementTree as ET
from pathlib import Path
from calendar import TextCalendar
from datetime import date, datetime

ZIPFILE_PATH = "./filesystem"
SOURCE_DIR = "./sample_filesystem"
CONFIG_PATH = "./config.csv"

class ShellEmulator:
    zipfile = None
    pwd = None
    

    def __init__(self, configfile) -> None:
        with open(configfile, 'r') as csvfile:
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                self.username, self.hostname, self.filesystem_path, self.logfile_path = row["username"], row["hostname"], Path(row["filesystem_path"]), Path(row["log_path"])

        self.zipfile = zipfile.ZipFile(self.filesystem_path, mode='a')
        self.pwd = zipfile.Path(self.zipfile)
        self.owners = dict()
        for file in self.zipfile.infolist():
            self.owners[file.filename] = (self.username, self.username + '_group')
        
        self.log = ET.Element("logs")
    
    def resolve_path(self, path: Path):
        temp = self.pwd
        for part in path.parts:
            if part == '/':
                temp = zipfile.Path(self.zipfile)
            elif part == '..':
                if temp == zipfile.Path(self.zipfile):
                    continue
                temp = temp.parent
            elif part == '.':
                continue
            else:
                temp = temp / part
                if not temp.is_dir() and not temp.is_file():
                    print(f'No such file or directory: {part}')
                    return
        return temp
    
    def format_path(self, path):
        format_path = path.relative_to(zipfile.Path(self.zipfile))
        if format_path == '.':
            format_path = ''
        if path.is_dir():
            format_path += '/'
        return format_path
    
    def ls(self, is_verbose=False) -> None:
        self.log_action('ls')
        for i in self.pwd.iterdir():
            if not is_verbose:
                print(i.name, end=' ')
            else:
                full_filename = self.format_path(self.resolve_path(Path(i.name)))
                info = self.zipfile.getinfo(full_filename)
                ownership = self.owners[full_filename]
                print(stat.filemode(info.external_attr >> 16), info.file_size, ownership[0], ownership[1], info.date_time, i.name, sep='\t')
        if not is_verbose:
            print('')
    
    def cd(self, dir) -> None:
        if not dir.is_dir():
            print('Not a directory:', dir)
        else:
            self.pwd = dir
    
    def chown(self, filepath, user, group):
        self.log_action('chown', f'{filepath} {user} {group}')
        self.owners[filepath] = (user, group)
    
    def rmdir(self, filepath):
        self.log_action('rmdir', str(filepath))
        if len(list(filepath.iterdir())) != 0:
            print('Directory not empty: aborting')
            return
        
        tmp_file = str(self.filesystem_path) + '.tmp.zip'
        tmp = zipfile.ZipFile(tmp_file, mode='w')
        filename = self.format_path(filepath)
        for file in self.zipfile.infolist():
            if file.filename != filename:
                tmp.writestr(file.filename, self.zipfile.read(file.filename))
        tmp.close()

        self.zipfile.close()
        shutil.move(tmp_file, self.filesystem_path)
        self.zipfile = zipfile.ZipFile(self.filesystem_path, mode='a')
        self.pwd = zipfile.Path(self.zipfile)
    
    def log_action(self, op, args=''):
        ET.SubElement(self.log, op, username=self.username, date=str(datetime.now())).text = args

    def close(self) -> None:
        tree = ET.ElementTree(self.log)
        tree.write(self.logfile_path)
        self.zipfile.close()


def main():
    shutil.make_archive(ZIPFILE_PATH, 'zip', SOURCE_DIR)
    shell = ShellEmulator(CONFIG_PATH)

    while True:
        cmd_full = input(f'{shell.username}@{shell.hostname}:{shell.format_path(shell.pwd)}$ ').split(' ')
        cmd = cmd_full[0]
        if len(cmd_full) > 1:
            args = cmd_full[1:]
        else:
            args = None

        if cmd == 'cd':
            if args != None:
                path = shell.resolve_path(Path(' '.join(args)))
                shell.cd(path)
            else:
                print('cd: missing 1 argument')
        elif cmd == 'ls':
            if args != None:
                tempdir = shell.pwd
                for arg in args:
                    if arg != '-l':
                        shell.cd(shell.resolve_path(Path(arg)))
                
                if '-l' in args:
                    shell.ls(is_verbose=True)
                else:
                    shell.ls()
                shell.pwd = tempdir
            else:
                shell.ls()
        elif cmd == 'rmdir':
            if args != None:
                shell.rmdir(shell.resolve_path(Path(' '.join(args))))
            else:
                print('rmdir: missing 1 argument')
        elif cmd == 'chown':
            if len(args) == 2:
                filename = shell.format_path(shell.resolve_path(Path(args[1])))
                user, group = args[0].split(':')
                shell.chown(filename, user, group)
            else:
                print('chown: missing 2 arguments')
        elif cmd == 'cal':
            if args != None:
                print(TextCalendar().formatyear(int(args[0])))
            else:
                print(TextCalendar().formatyear(date.today().year))
        elif cmd == 'exit':
            shell.close()
            break


if __name__ == "__main__":
    main()