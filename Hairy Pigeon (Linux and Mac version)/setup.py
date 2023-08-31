import os
import shutil
import subprocess
import errno

print('Installing...')

olddir = os.getcwd()
scriptdir = __file__[:__file__.rindex('/')]
os.chdir(scriptdir)

compilerfolder = os.path.expanduser('~/hairypigeon')

def copyanything(src, dst):
    if os.path.exists(dst):
        try : os.remove(dst)
        except : shutil.rmtree(dst)
    try:
        shutil.copytree(src, dst)
    except OSError as exc: # python >2.5
        if exc.errno in (errno.ENOTDIR, errno.EINVAL):
            shutil.copy(src, dst)
        else: raise

def copy(src, dst, name):
    copyanything(src + '/' + name, dst + '/' + name)

try: os.mkdir(compilerfolder)
except: pass

copy('.', compilerfolder, 'main.py')
copy('.', compilerfolder, 'CompilerParts')

os.chdir(f'{compilerfolder}/CompilerParts')

def compile(compiler, input, output, args=''):
    subprocess.Popen(f'{compiler} {input} -O3 {args} -o {output}', shell=True).wait()

compile('g++ -std=c++20', 'SEIR.cpp', 'seir')
compile('g++ -std=c++20', 'SEIRC.cpp', 'seirc')
compile('gcc', 'file.c', 'file.o', args='-c')
compile('gcc', 'onlyshowerr.c', 'onlyshowerr')

for f in ['.bashrc', '.zshrc'] : subprocess.Popen(f'printf "\\nalias pigeon=\'python3 {compilerfolder}/main.py \'\\n" >> ~/{f}', shell=True).wait()

os.chdir(olddir)

print('Done')
