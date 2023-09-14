import shutil
import os
import sys
import glob
import subprocess
import errno
from pathlib import Path  

cc = 'gcc'
ccpp = 'g++'

def touch(path):
    try:
        with open(path, 'a') as _ : pass
    except : pass

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
    Path(dst).mkdir(parents=True, exist_ok=True)
    copyanything(src + '/' + name, dst + '/' + name)

cptocd = [
    'hp',
    'seir',
    'seirc',
    #'removewarnings',
    'onlyshowerr',
    'hairypidgeon.py',
    '__init__.py',
    'file.o',
    'alloc.c',
    'file.c',
]

originaldir = os.getcwd()
scriptdir = __file__[:__file__.rindex('/')]

args = sys.argv[1:]

rename = None

flags = []
argscopy = args[:]
for i in range(len(args)):
    a = argscopy[i]
    if a[0] == '-':
        flags.append(a)
        n = args.index(a)
        args.pop(n)
        if a == '-o':
            try:
                rename = args[n]
                args.pop(n)
            except:
                print('no output file name provided')
                sys.exit(1)

def getext(name) :
    return Path(name).suffix[1:]

def extractbyext(ext, args=args):
    if not isinstance(ext, list) : ext = [ext]
    result = []
    for e in ext:
        for a in args[:]:
            if '.' in a and getext(a) == e:
                result.append(a)
                args.pop(args.index(a))
    return result

cfiles = extractbyext(['c', 'h'])
cppfiles = extractbyext(['cpp', 'hpp'])
ofiles = extractbyext('o')

rc = subprocess.Popen('nasm -v >/dev/null 2>&1', shell=True).wait()
if rc != 0 and not '-O' in flags:
    print("nasm isn't installed. Try installing nasm or compiling with -O.")
    sys.exit(1)

for s in cptocd:
    copy(f'{scriptdir}/CompilerParts', f'{scriptdir}/CompileDirectory', s)
    os.chmod(f'{scriptdir}/CompileDirectory/{s}', 0o755)

import CompileDirectory.hairypidgeon as compiler

tocomp = args[0]
outname = tocomp[:tocomp.rindex('.')]

os.chdir(f'{scriptdir}/CompileDirectory')

copy(originaldir, f'{scriptdir}/CompileDirectory', tocomp)

def copyuses(tocomp):
    tcsrc = open(tocomp).read()
    for line in tcsrc.split('\n'):
        line = line.strip()
        if line.startswith('use') and line[3:].strip()[0] == '"':
            fname = line[line.index('"')+1:line.rindex('"')]
            copy(originaldir, f'{scriptdir}/CompileDirectory', fname)
            copyuses(fname)

copyuses(tocomp)

isoptimize = '-O' in flags
ismakeobject = '-c' in flags
consumec = cfiles or cppfiles
obj = compiler.start(tocomp, optimize=isoptimize, ismakeobject=(ismakeobject or consumec))
cargs = obj['cargs']
for s in cargs.split(' ') + cfiles + cppfiles:
    if getext(s) in ['o', 'c', 'h', 'cpp', 'hpp'] : copy(originaldir, f'{scriptdir}/CompileDirectory', s)

objectstr = '-c' if ismakeobject or consumec else ''
if isoptimize : command = f"{cc} -O3 rout.c {objectstr} {cargs} 2>&1 | ./onlyshowerr"
else : command = f"nasm -fmacho64 rout.asm && clang -Wl,-no_pie file.o rout.o {objectstr} {cargs} 2>&1 | ./onlyshowerr"
subprocess.Popen(command, shell=True).wait()

if consumec:
    procs = []
    objs = ['rout.o']
    #cheaders = extractbyext('h', cfiles)
    ccodes = extractbyext('c', cfiles)
    cppcodes = extractbyext('cpp', cppfiles)
    i = 0
    for f in ccodes:
        n = f'c{i}.o'
        i += 1
        command = f"{cc} -O3 -c {f} -o {n}"
        procs.append(subprocess.Popen(command, shell=True))
        objs.append(n)
    for f in cppcodes:
        n = f'c{i}.o'
        i += 1
        command = f"{ccpp} -O3 -c {f} -o {n}"
        procs.append(subprocess.Popen(command, shell=True))
        objs.append(n)
    for p in procs : p.wait()
    if cppcodes : cc = ccpp
    command = f"{cc} {' '.join(objs)} 2>&1 | ./onlyshowerr"
    subprocess.Popen(command, shell=True).wait()

cwd = os.getcwd()
touch(cwd + '/a.out')
shutil.copyfile(cwd + '/a.out', cwd + '/' + outname)

if rename:
    shutil.copyfile(cwd + '/' + outname, cwd + '/' + rename)
    outname = rename

copy(cwd, originaldir, outname)

if '-S' in flags:
    if '-O' in flags:
        subprocess.Popen(f'{cc} -O3 -S -masm=intel rout.c 2>&1 | ./onlyshowerr', shell=True).wait()
        shutil.copyfile(cwd + '/rout.s', cwd + '/rout.asm')
    shutil.copyfile(cwd + '/rout.asm', cwd + '/' + outname + '.asm')
    copy(cwd, originaldir, outname + '.asm')

if ismakeobject:
    shutil.copyfile(cwd + '/rout.o', cwd + '/' + outname + '.o')
    copy(cwd, originaldir, outname + '.o')

files = glob.glob(f'{scriptdir}/CompileDirectory/*')
for f in files:
    #if False:
        try: os.remove(f)
        except: pass

os.chdir(originaldir)
os.chmod(f'./{outname}', 0o755)

if '-run' in flags:
    os.chdir(originaldir)
    subprocess.Popen(f'./{outname}', shell=True).wait()