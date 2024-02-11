import os
import shutil
import subprocess
import errno

print('Installing...')

olddir = os.getcwd()
try : scriptdir = __file__[:__file__.rindex('/')]
except : scriptdir = __file__
try : os.chdir(scriptdir)
except : pass

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

hpf = open('hp').read()
libfns = []
for line in hpf.split('\n'):
    sp = line.lstrip().split(' ')
    if len(sp) >= 2 and sp[0] == 'fn' : libfns.append(sp[1])
libfns = list(set(libfns))
libfns.sort()
with open('libfns.txt', 'w') as f : f.write('\n'.join(libfns))

def compile(compiler, input, output, args=''):
    return subprocess.Popen(f'{compiler} {input} -O3 {args} -o {output}', shell=True)

comps = []
comps.append(compile('g++ -std=c++20', 'SEIR.cpp', 'seir'))
comps.append(compile('g++ -std=c++20', 'SEIRC.cpp', 'seirc'))
comps.append(compile('gcc', 'file.c', 'file.o', args='-c'))
comps.append(compile('gcc', 'onlyshowerr.c', 'onlyshowerr'))
for c in comps : c.wait()

for f in ['.bashrc', '.zshrc'] : subprocess.Popen(f'printf "\\nalias pigeon=\'python3 {compilerfolder}/main.py \'\\n" >> ~/{f}', shell=True).wait()

os.chdir(os.path.expanduser('~'))

with open('pigeon', 'w') as f:
    f.write("""
        #!/usr/bin/env bash
        python3 ~/hairypigeon/main.py "$@"
    """)

os.chdir(olddir)

print('Done')
