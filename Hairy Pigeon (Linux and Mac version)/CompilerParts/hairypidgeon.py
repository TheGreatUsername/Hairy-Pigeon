import re
import sys
import subprocess
import struct

def tokenize(src):
    result = re.findall(r'###|#[^\n]*|\.\(|\{|\}| \[|\[|\]|\(|\)|\$"[^"]*"|"[^"]*"|\'[^\']+\'|`[^`]*`|\-[\d]+|[\w_]+|[^\w_\s\(\)\[\]\{\}]+|\n|\S', src+'\n')
    oldresult = result
    result = []
    incomment = False
    for t in oldresult:
        if t == '###' : incomment = not incomment
        if not incomment and t != '###' or t == '\n' : result.append(t)
    result = [t for t in result if t[0] != '#']
    return ['\n'] + result + ['\n', '\n']
    
toki = 0
tokens = []

def toptok():
    t = tokens[toki]
    if t == ';' : return '\n'
    return t
    
def getok():
    global toki
    result = toptok()
    toki += 1
    return result

def eof():
    return toki >= len(tokens) - 1

idi = 0
def newid(name):
    global idi
    result = f"@{name}_{idi}"
    idi += 1
    return result

allocfunc = 'aalloc'
freefunc = 'afree'
def usecmalloc():
    global allocfunc
    global freefunc
    allocfunc = 'malloc'
    freefunc = 'free'
#usecmalloc()

fnkey = 'fn'
forkey = 'for'
copykey = 'copy'
dropkey = 'drop'
sizeofkey = 'sizeof'
cfkey = 'cf'
intkey = 'int'
chrkey = 'chr'
fltkey = 'flt'
voidkey = 'void'
memkey = 'mem'
eqtypekey = 'eqtype'
weakcastkey = 'weakcast'
memindexkey = 'memindex'
memindexsetkey = 'memindexset'
usekey = 'use'
glokey = 'glo'
breakkey = 'break'
dollarkey = '$'
notkey = 'not'
fpkey = '&'
fpexeckey = '*'
lambdakey = 'lambda'
haspropkey = 'hasprop'
casekey = 'case'
pragmakey = 'pragma'
importkey = 'import'
nomanglekey = 'export'
iskey = 'is'
argckey = 'sys_argc'
argvkey = 'sys_argv'
allockey = 'sys_alloc'
freekey = 'sys_free'
structtostrkey = 'sys_structtostr'
vgetkey = 'sys_vget'
vsetkey = 'sys_vset'
rettypekey = '->'
typekeys = [intkey, chrkey, fltkey, voidkey, memkey]
types = {typekeys[i] : i for i in range(len(typekeys))}
ops = ['+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>=']
boolops = ['and', 'or']
decfunctypes = {}
functypes = {}
funcargs = {}
funcargnames = {}
funclocs = {}
funcvars = {}
funccopyvars = {}
importedfuncs = []
output = ''
outstk = []
curvars = {}
constvars = []
structsizes = {}
structprops = {}
structtraits = {}
todrop = {}
glos = []
glotypes = {}
vectypes = []
maptypes = []
curfunc = ''

def out(s):
    global output
    output += str(s) + ' '

def outlp() : out('(')
def outrp() : out(')')

def pushout():
    global output
    outstk.append(output)
    output = ''
    
def popout():
    global output
    result = output
    output = outstk.pop()
    return result

def getln():
    ln = 0
    for i in range(toki):
        if tokens[i] == '\n' : ln += 1
    return ln

def err(s):
    ln = getln()
    print(f"Error: {s} in line {ln}")
    try:
        seg = tokens[toki-5:toki+5]
        seg = [t if t != '\n' else '\\n' for t in seg]
        print(f"at: {' '.join(seg)}")
        off = 4
        print(' ' * 4 + ' ' * (sum([len(s) for s in seg[:off]]) + off) + '^')
    except : pass
    #int('a')
    sys.exit(1)
    
def expect(e, f):
    err(f"expected '{e}' found '{f}'")
    
def match(s):
    t = getok()
    if t != s : expect(s, t)

def hashstr(s):
    s = str(s)
    hash = 5381
    for c in s:
        hash = (((hash << 5) + hash) + ord(c)) % 100000000000
    return hash

def hashlist(l):
    hash = 0
    for e in l : hash += hashstr(e)
    return hash

def hashfunc(name, types):
    hash = hashlist([name] + types)
    return hash

fphashes = {}
fpargsmap = {}
def hashfp(name, types):
    r = getfunctype(name, types)
    types.append(r)
    hash = hashlist(types + ['fp'])
    fphashes[hash] = r
    fpargsmap[hash] = types[:-1]
    return hash
    
def isfp(t):
    return t in fphashes
    
def fpret(t):
    return fphashes[t]
    
def fpargs(t):
    return fpargsmap[t]
    
def hashstruct(args, types):
    hash = hashlist(args + types)
    return hash
    
def newstruct(args, atypes):
    hash = hashstruct(args, atypes)
    types[f"struct_{hash}"] = hash
    structsizes[hash] = sum([gettypesize(t) for t in atypes])
    structprops[hash] = [(args[i], atypes[i]) for i in range(len(args))]

def getstructproptype(hash, name):
    props = structprops[hash]
    for p in props:
        if p[0] == name : return p[1]

def getstructpropoffset(hash, name):
    props = structprops[hash]
    offset = 0
    for p in props:
        if p[0] != name : offset += 1 #gettypesize(p[1])
        else : break
    return offset

def getstructsize(hash):
    props = structprops[hash] 
    offset = 0 
    for p in props: 
        offset += gettypesize(p[1])  
    return offset

def isstruct(t):
    return t in structprops

def structhastrait(hash, name):
    for t in structtraits[hash]:
        if t[0] == name : return True
    return False

def getstructtrait(hash, name):
    for t in structtraits[hash]:
        if t[0] == name : return t

def setfunctype(name, types, t):
    hash = hashfunc(name, types)
    functypes[hash] = t
    
def setdecfunctype(name, type):
    decfunctypes[name] = type
    
def setfuncargs(name, args):
    funcargs[name] = args
    
def getfuncargs(name):
    return funcargs[name]
    
def getfunctype(name, types):
    if name in decfunctypes : return decfunctypes[name]
    return functypes[hashfunc(name, types)]

def isfunccompiled(name, types):
    return hashfunc(name, types) in functypes

def hasfunc(name) : return name in funcargs

def manglefunc(name, types):
    return f"@{name}_{hashfunc(name, types)}"
    
def getfp(name, types):
    return manglefunc(name, types) + '_fp'

def addimportedfunc(name):
    importedfuncs.append(name)

def isimportedfunc(name):
    return name in importedfuncs
    
def gettypesize(t):
    if t == types[chrkey] : return 1
    elif t == types[voidkey] : return 0
    elif t in [types[k] for k in typekeys] : return 8
    elif t in structsizes : return structsizes[t]
    elif isfp(t) : return 8
    else : err(f"cannot get size of type '{t}'")
    
def gettype():
    pushout()
    result = expr()
    popout()
    return result
    
def typetotext(t):
    if t in vectypes:
        return f'vec {typetotext(getstructproptype(t, "t"))}'
    for e in types:
        if t == types[e] : return e
    
def skipblock():
    if toptok() == '{':
        getok()
        depth = 1
        while depth > 0:
            if toptok() == '{' : depth += 1
            elif toptok() == '}' : depth -= 1
            getok()
    else:
        while toptok() != '\n' : getok()
    
def dofunc():
    while toptok() != '=' : getok()
    getok()
    skipblock()
    
def isint(n):
    try:
        int(n)
        return True
    except : return False
    
def double_to_hex(f):
    return hex(struct.unpack('<Q', struct.pack('<d', f))[0])

def donum(n):
    if toptok() == '.':
        getok()
        dec = getok()
        if not isint(dec):
            err(f"malformed number '{n}.{dec}'")
        f = float(f'{n}.{dec}')
        out(double_to_hex(f))
        return types[fltkey]
    else:
        out(n)
        return types[intkey]

def drop(v, type):
    if isstruct(type):
        props = structprops[type]
        out(f"(? {v} (" + "{}")
        if structhastrait(type, dropkey):
            #oldft = getfunctype(dropkey, [type])
            setdecfunctype(dropkey, types[voidkey])
            compilefunc(dropkey, [type], at=getstructtrait(type, dropkey)[1]) 
            #setdecfunctype(dropkey, oldft)
            mf = manglefunc(dropkey, [type])
            out(f"({mf} {v})")
        for p in props:
            if isstruct(p[1]):
                drop(f"(!! {v} {getstructpropoffset(type, p[0])} 8)", p[1])
        out(f"(@ {freefunc} {v})")
        out(") 0)")
    else:
        #out(f"(@ free {v})")
        out(0)

def copy(v, type):
    if isstruct(type) and structhastrait(type, copykey):
        out('({}')
        compilefunc(copykey, [type], at=getstructtrait(type, copykey)[1])
        mf = manglefunc(copykey, [type])
        out(f"({mf} {v})")
        outrp()
    elif isstruct(type):
        out("({}")
        tocopy = newid("tocopy")
        result = newid("copy")
        out(f"(= {tocopy} {v})")
        out(f"(= {result} (@ {allocfunc} {getstructsize(type)}))")
        props = structprops[type]
        for i in range(len(props)):
            p = props[i]
            arg = f"(!! {tocopy} {i} 8)"
            out(f"(!: {result} {i} 8")
            copy(arg, p[1])
            outrp()
        out(result)
        outrp()
    else:
        out(v)

voidid = types[voidkey]
def compilefunc(name, types, at=None, isnomangle=False):
    if isfunccompiled(name, types) and getfunctype(name, types) == None:
        err(f"Return type needed for func '{name}'")
    if not isfunccompiled(name, types) or isnomangle:
        global toki
        global curvars
        global constvars
        global todrop
        global curfunc
        oldtoki = toki
        oldcurvars = curvars.copy()
        oldconstvars = constvars.copy()
        oldtodrop = todrop.copy()
        oldcurfunc = curfunc
        constvars = []
        toki = funclocs[name]
        curfunc = name
        if at != None:
            toki = at
        todrop = {}
        setfunctype(name, types, None)
        fp = getfp(name, types)
        out(f"(:= {fp}")
        outlp()
        if isnomangle:
            out('<>>')
            out(name)
        else:
            out("<>")
            out(manglefunc(name, types))
        outlp()
        args = []
        while toptok() not in [rettypekey, '=']:
            t = getok()
            if t != '^':
                out(t)
                args.append(t)
        funcargnames[name] = args[:]
        outrp()
        if toptok() == rettypekey:
            while toptok() != '=' : getok()
        getok()
        vars = funcvars[name]
        copyvars = funccopyvars[name]
        for i in range(len(args)):
            vars[i] = args[i]
            #if vars[i] in copyvars : compilefunc('clone', [types[i]])
        curvars = {v : None for v in vars}
        skipdropinit = []
        for i in range(len(vars)):
            v = vars[i]
            if i < len(types):
                curvars[v] = types[i]
                if v in copyvars:
                    #compilefunc('clone', [types[i]])
                    t = types[i]
                    out(f"(= {v}")
                    copy(v, t)
                    outrp()
                    if isstruct(t):
                        dropid = newid("todrop")
                        out(f"(= {dropid} {v})")
                        todrop[dropid] = t
                        skipdropinit.append(dropid)
                else:
                    out(f"(= {v} {v})")
            elif not v in args:
                out(f"(= {v} {0})")
        pushout()
        resultid = newid('result')
        out(f"(= {resultid}")
        t = expr()
        outrp()
        et = getfunctype(name, types)
        if name == copykey:
            et = types[0]
        if et != None and et != voidid:
            if t != et : expect(typetotext(et), typetotext(t))
        setfunctype(name, types, t)
        if name == 'vec':
            vectypes.append(t)
        elif name == 'map':
            maptypes.append(t)
        if isstruct(t) and name not in [copykey, '[]']:
            out(f"(= {resultid}")
            copy(resultid, t)
            outrp()
        if name != copykey:
            for v in todrop:
                drop(v, todrop[v])
        out(resultid)
        s = popout()
        for v in todrop:
            if v not in skipdropinit : out(f"(= {v} {0})")
        out(s)
        outrp()
        outrp()
        toki = oldtoki
        curvars = oldcurvars
        constvars = oldconstvars
        todrop = oldtodrop
        curfunc = oldcurfunc
        
def docall(name):
    argnum = getfuncargs(name)
    pushout()
    outlp()
    out('{}')
    pushout()
    types = []
    for i in range(argnum):
        types.append(expr())
    outrp()
    args = popout()
    compilefunc(name, types)
    outlp()
    out(name if isimportedfunc(name) else manglefunc(name, types))
    out(args)
    outrp()
    s = popout()
    t = getfunctype(name, types)
    if isstruct(t):
        dropid = newid("todrop")
        out("({}")
        drop(dropid, t)
        out(f"(= {dropid} {s})")
        outrp()
        todrop[dropid] = t
    else : out(s)
    return t

def docf():
    match('(')
    outlp()
    out('@')
    name = getok()
    out(name)
    while toptok() != ')':
        expr()
    match(')')
    outrp()
    return types[memkey]

def docstr(s):
    out(f'"{s[1:-1]}"')
    return types[memkey]

def dovar(v):
    if curvars[v] == None:
        err(f"variable '{v}' used before assignment")
    out(v)
    return curvars[v]

def skipnl():
    while not eof() and toptok() == '\n' : getok()

def doblock():
    result = types[voidkey]
    skipnl()
    outlp()
    out('{}')
    while toptok() != '}':
        result = expr()
        if toptok() != '}' : match('\n')
        skipnl()
    getok()
    outrp()
    return result

def dounderscore():
    out('1')
    return types[intkey]

def doguard():
    global toki
    result = None
    pushout()
    expr()
    cond = popout()
    if isint(cond) and int(cond) != 0:
        match(':')
        pushout()
        t = expr()
        s = popout()
        oldtoki = toki
        if toptok() == '\n' : getok()
        if toptok() == '|' :
            getok()
            out(f'(? 1 {s}')
            doguard()
            outrp()
        else:
            out(s)
            toki = oldtoki
            #out('0')
        return t
    if isint(cond) and int(cond) == 0:
        match(':')
        if toptok() == '{':
            skipblock()
        else:
            while toptok() != '\n' : getok()
        oldtoki = toki
        if toptok() == '\n' : getok()
        result = voidid
        if toptok() == '|' :
            getok()
            result = doguard()
        else:
            toki = oldtoki
            out('0')
        return result
    out('(?')
    out(cond)
    match(':')
    t = expr()
    if result == None : result = t
    elif result != t : result = types[voidkey]
    oldtoki = toki
    if toptok() == '\n' : getok()
    if toptok() == '|' :
        getok()
        t = doguard()
        if result != t : result = types[voidkey]
    else:
        toki = oldtoki
        out('0')
    outrp()
    return result

def dotypekey(k):
    out('0')
    return types[k]

def doeqtype(key):
    if key == eqtypekey:
        a = gettype()
        b = gettype()
        out('1' if a == b else '0')
    elif key == haspropkey:
        a = gettype()
        b = getok()
        out('1' if isstruct(a) and getstructproptype(a, b) != None else '0')
    return types[intkey]

escmap = {
    't' : 9,
    'n' : 10,
    '\\' : ord('\\'),
    '0' : 0,
}
def dochar(t):
    c = t[1:-1]
    if len(c) == 1 or len(c) == 2 and c[0] == '\\':
        if len(c) == 1:
            out(ord(c))
        else:
            if not c[1] in escmap:
                err(f"invalid escape char '{c[1]}'")
            out(escmap[c[1]])
    else : err(f"malformed char '{c}'") 
    return types[chrkey]

def doweakcast():
    t = gettype()
    expr()
    return t

intid = types[intkey]
def dosquarebrace():
    skipnl()
    global toki
    oldtoki = toki
    isastruct = toptok() == usekey
    getok()
    if not isastruct : isastruct = toptok() == '='
    toki = oldtoki
    if isastruct:
        return dostruct()
    isspread = toptok() == '...'
    if isspread : getok()
    pushout()
    t = expr()
    s = popout()
    if isspread:
        if t in maptypes:
            return domap(s, t, isspread=isspread)
        elif t in vectypes:
            return dovec(s, t, isspread=isspread)
        elif isstruct(t):
            return dostruct(base=(s, t))
        else:
            err(f"cannot spread type '{typetotext(t)}'")
    elif toptok() == ':':
        return domap(s, t, isspread=isspread)
    else:
        return dovec(s, t, isspread=isspread)
        
def domap(fs, ft, isspread=False):
    out('({}')
    resultid = newid('map')
    if isspread:
        kat = getstructproptype(ft, 'keys')
        kt = getstructproptype(kat, 't')
        vat = getstructproptype(ft, 'values')
        vt = getstructproptype(vat, 't')
        keytypes = [kt, ft]
        valtypes = [vt, None]
        keyargs = [f"(!! (!! {fs} {getstructpropoffset(ft, 'keys')} 8) {getstructpropoffset(kat, 't')} 8)", fs]
        valargs = [f"(!! (!! {fs} {getstructpropoffset(ft, 'values')} 8) {getstructpropoffset(vat, 't')} 8)", "0"]
        ft = kt
    else:
        keytypes = [ft]
        keyargs = [fs]
        match(':')
        pushout()
        valtypes = [expr()]
        valargs = [popout()]
    name = 'map'
    mapdectypes = [keytypes[0], valtypes[0]]
    compilefunc(name, mapdectypes)
    vt = getfunctype(name, mapdectypes)
    compilefunc('mextend', [vt, vt])
    mt = vt
    mapsettypes = [vt] + mapdectypes
    compilefunc('mset', mapsettypes)
    key0id = newid('key0')
    out(f'(= {key0id} {keyargs[0]})')
    val0id = newid('val0')
    out(f'(= {val0id} {valargs[0]})')
    keyargs[0] = key0id
    valargs[0] = val0id
    out(f"(= {resultid} ({manglefunc(name, mapdectypes)} {key0id} {val0id}))")
    if toptok() == ',' : getok()
    skipnl()
    while toptok() != ']':
        if toptok() == '...':
            getok()
            pushout()
            keytypes.append(expr())
            keyargs.append(popout())
            valtypes.append(None)
            valargs.append('0')
        else:
            pushout()
            keytypes.append(expr())
            keyargs.append(popout())
            match(':')
            pushout()
            valtypes.append(expr())
            valargs.append(popout())
        if toptok() == ',' : getok()
        skipnl()
    for i in range(1 if isspread else 0, len(keyargs)):
        ka = keyargs[i]
        kt = keytypes[i]
        va = valargs[i]
        vt = valtypes[i]
        if kt == mt:
            out(f"({manglefunc('mextend', [mt, mt])} {resultid} {ka})")
        else:
            if kt != ft:
                typemismatch(ft, kt)
            if vt != valtypes[0]:
                typemismatch(valtypes[0], vt)
            out(f"({manglefunc('mset', mapsettypes)} {resultid} {ka} {va})")
    match(']')
    out(resultid)
    outrp()
    return mt
    
def dovec(fs, ft, isspread=False):
    out('({}')
    resultid = newid('vec')
    types = [ft]
    args = [fs]
    name = 'vec'
    vt = ft
    if isspread:
        #compilefunc('clone', [vt])
        vt = ft
        ft = getstructproptype(vt, 't')
        types = [vt]
    else:
        compilefunc(name, types)
        vt = getfunctype(name, types)
    compilefunc('vpush', [vt, ft])
    compilefunc('vextend', [vt, vt])
    firstvalid = newid('firstval')
    out(f'(= {firstvalid} {fs})')
    args[0] = firstvalid
    if isspread:
        out(f"(= {resultid} ({manglefunc(name, [ft])} (!! {args[0]} {getstructpropoffset(vt, 't')} 8)))")
    else:
        out(f"(= {resultid} ({manglefunc(name, types)} {args[0]}))")
    if toptok() == ',' : getok()
    skipnl()
    while toptok() != ']':
        if toptok() == '...':
            getok()
            pushout()
            types.append(expr())
            args.append(popout())
            if toptok() == ',' : getok()
            skipnl()
        else:
            pushout()
            types.append(expr())
            args.append(popout())
            if toptok() == ',' : getok()
            skipnl()
    for i in range(len(args)):
        a = args[i]
        t = types[i]
        if t == ft:
            out(f"({manglefunc('vpush', [vt, ft])} {resultid} {a})")
        elif t == vt:
            out(f"({manglefunc('vextend', [vt, vt])} {resultid} {a})")
        else:
            typemismatch(ft, t)
    match(']')
    out(resultid)
    outrp()
    return vt
        
memtype = types[memkey]
def dostruct(base=None):
    args = ['_']
    types = [intid]
    decs = ['0']
    traits = []
    out('({}')
    if base != None:
        ps = base[0]
        t = base[1]
        s = newid('spreadedstruct')
        out(f"(= {s} {ps})")
        newprops = structprops[t]
        for p in newprops:
            name = p[0]
            type = p[1]
            if name in args:
                ind = args.index(name)
                args[ind] = name
                types[ind] = type
                decs[ind] = f"(!! {s} {getstructpropoffset(t, name)} 8)"
            else:
                args.append(name)
                types.append(type)
                decs.append(f"(!! {s} {getstructpropoffset(t, name)} 8)")
        if toptok() != ']':
            if toptok() == '\n' : skipnl()
            else : match(',')
            skipnl()
    while toptok() != ']':
        if toptok() == 'fn':
            global toki
            getok()
            if toptok().strip() == '[':
                getok()
                match(']')
                curtoki = toki
                name = '[]'
                if toptok() == '=':
                    getok()
                    curtoki = toki
                    name = '[]='
                    getok()
                getok()
            elif toptok() in ops:
                name = getok()
                curtoki = toki
                getok()
            else:
                name = getok()
                curtoki = toki
            traits.append((name, curtoki))
            getok()
            match('=')
            match('{')
            toki -= 1
            skipblock()
        elif toptok() == usekey:
            getok()
            if toptok() == '...':
                getok()
                for v in curvars:
                    if curvars[v] != None:
                        name = v
                        t = curvars[v]
                        args.append(name)
                        types.append(t)
                        decs.append(v)
            else:
                while toptok() not in [',', '\n', ']']:
                    name = toptok()
                    pushout()
                    t = expr()
                    s = popout()
                    if name in args:
                        ind = args.index(name)
                        args[ind] = name
                        types[ind] = t
                        decs[ind] = s
                    else:
                        args.append(name)
                        types.append(t)
                        decs.append(s)
        elif toptok() == '...':
            getok()
            pushout()
            t = expr()
            ps = popout()
            s = newid('spreadedstruct')
            out(f"(= {s} {ps})")
            newprops = structprops[t]
            for p in newprops:
                name = p[0]
                type = p[1]
                if name in args:
                    ind = args.index(name)
                    args[ind] = name
                    types[ind] = type
                    decs[ind] = f"(!! {s} {getstructpropoffset(t, name)} 8)"
                else:
                    args.append(name)
                    types.append(type)
                    decs.append(f"(!! {s} {getstructpropoffset(t, name)} 8)")
        else:
            name = getok()
            match('=')
            pushout()
            t = expr()
            s = popout()
            if name in args:
                ind = args.index(name)
                args[ind] = name
                types[ind] = t
                decs[ind] = s
            else:
                args.append(name)
                types.append(t)
                decs.append(s)
        if toptok() != ']':
            if toptok() == '\n' : skipnl()
            else : match(',')
    getok()
    hash = hashstruct(args, types)
    prevexisted = isstruct(hash)
    newstruct(args, types)
    structtraits[hash] = traits
    structsize = getstructsize(hash)
    sl = newid('struct')
    drop(sl, hash)
    out(f"(= {sl} (@ {allocfunc} {structsize}))")
    for i in range(len(args)):
        #offset = getstructpropoffset(hash, args[i])
        size = 8 #gettypesize(types[i])
        out(f"(!: {sl} {i} {size}")
        copy(decs[i], types[i])
        #out(decs[i])
        outrp()
    if not 'strfmt' in args and not prevexisted:
        out(f'(<> sys_struct{hash}tostr (struct)')
        compilefunc('str', [])
        out(f'(= result ({manglefunc("str", [])}))')
        strtype = getfunctype('str', [])
        compilefunc('vextend', [strtype, strtype])
        compilefunc('cstrtovec', [memtype])
        for i in range(1, len(args)):
            size = 8
            compilefunc('tostr', [types[i]])
            tmp = newid('tmp')
            if i == 1:
                out(f'({manglefunc("vextend", [strtype, strtype])}')
                out('result')
                out(f'(= {tmp} ({manglefunc("cstrtovec", [memtype])} "[")')
                outrp()
                outrp()
                drop(tmp, strtype)
            out(f'({manglefunc("vextend", [strtype, strtype])}')
            out('result')
            out(f'(= {tmp} ({manglefunc("cstrtovec", [memtype])} "{args[i]} = "))')
            outrp()
            drop(tmp, strtype)
            out(f'({manglefunc("vextend", [strtype, strtype])}')
            out('result')
            out(f'(= {tmp} ({manglefunc("tostr", [types[i]])}')
            out(f"(!! struct {i} {size})")
            outrp()
            outrp()
            outrp()
            drop(tmp, strtype)
            if i != len(args)-1:
                out(f'({manglefunc("vextend", [strtype, strtype])}')
                out('result')
                out(f'(= {tmp} ({manglefunc("cstrtovec", [memtype])} ", ")')
                outrp()
                outrp()
                drop(tmp, strtype)
            else:
                out(f'({manglefunc("vextend", [strtype, strtype])}')
                out('result')
                out(f'(= {tmp} ({manglefunc("cstrtovec", [memtype])} "]")')
                outrp()
                outrp()
                drop(tmp, strtype)
        out('result')
        outrp()
    elif not prevexisted:
        out(f'(<> sys_struct{hash}tostr (struct) 0)')
    out(sl)
    outrp()
    todrop[sl] = hash
    return hash

def doparens():
    result = expr()
    match(")")
    return result

def doassign(v):
    if v in constvars:
        err(f"cannot reassign to constant '{v}'")
    if curfunc != '' and v in funcargnames[curfunc]:
        err(f"cannot reassign to function parameter '{v}'")
    assignkey = getok()
    if assignkey == iskey:
        constvars.append(v)
    try : type = curvars[v]
    except : type = None
    pushout()
    result = expr()
    e = popout()
    if type == None:
        curvars[v] = result
    elif type != result:
        expect(typetotext(type), typetotext(result))
    assignbycopy = curfunc != copykey and isstruct(curvars[v]) and (curfunc == '' or v not in funcargnames[curfunc])
    #assignbycopy = False
    if assignbycopy : todrop[v] = curvars[v]
    tmpvar = newid('todropafterassignment')
    out('({}')
    if assignbycopy : out(f'(= {tmpvar} {v})')
    out(f'(= {v}')
    if assignbycopy : copy(e, result)
    else : out(e)
    outrp()
    if assignbycopy : drop(tmpvar, curvars[v])
    out(v)
    outrp()
    return result

def domemindex():
    out('(!!')
    expr()
    expr()
    expr()
    outrp()
    return types[voidkey]
    
def domemindexset(): 
    out('(!:') 
    expr() 
    expr() 
    expr() 
    expr() 
    outrp()
    return types[voidkey]

def dosizeof():
    t = gettype()
    if isstruct(t):
        out(getstructsize(t))
    else : out(8)
    return types[intkey]

def docopy():
    v = newid('tocopy')
    out('({}')
    out(f'(= {v}')
    t = expr()
    outrp()
    copy(v, t)
    outrp()
    return t

def dodrop(): 
    v = newid('todrop') 
    out('({}') 
    out(f'(= {v}') 
    t = expr() 
    outrp() 
    drop(v, t) 
    outrp() 
    return types[voidkey]

def dofor():
    global curvars
    global toki
    args = []
    pushout()
    v = toptok()
    if v in curvars and curvars[v] != None or not v.isalnum():
        t = expr()
        s = popout()
    else:
        t = types[intkey]
        s = v
        curvars[s] = t
        getok()
        popout()
    args.append((s, t))
    v = toptok()
    if False and toptok() != ':':
        pushout()
        if v in curvars and curvars[v] != None or not v.isalnum():
            #print('hi', v, v in curvars, curvars)
            t = expr()
            s = popout()
        else:
            t = types[intkey]
            s = v
            curvars[s] = t
            getok()
            popout()
        args.append((s, t))
    while toptok() != ':':
        pushout()
        t = expr()
        s = popout()
        args.append((s, t))
    getok()
    if len(args) == 1:
        out('(??')
        out(args[0][0])
        expr()
        outrp()
    else:
        out('({}')
        iterid = args[0][0] #newid('iter')
        maxid = newid('max')
        stepid = newid('step')
        eachassign = None
        trait = '[]'
        if len(args) == 2 and isstruct(args[1][1]) and structhastrait(args[1][1], trait):
            name = 'len'
            offset = getstructpropoffset(args[1][1], name) 
            t = getstructproptype(args[1][1], name)
            eachid = iterid 
            iterid = newid('iter') 
            out(f"(= {iterid} 0) (= {maxid} (!! {s} {offset} 8)) (= {stepid} 1)")
            pushout()
            out(f'(= {eachid}' + '({}')
            targs = [args[1][1], types[intkey]]
            compilefunc(trait, targs, at=getstructtrait(args[1][1], trait)[1])
            mf = manglefunc(trait, targs)
            out(f"({mf} {args[1][0]} {iterid})")
            outrp()
            outrp()
            t = getfunctype(trait, targs)
            curvars[eachid] = t
            eachassign = popout()
        elif len(args) == 2 and isstruct(args[1][1]):
            oldcurvars = curvars.copy()
            oldtoki = toki
            props = structprops[args[1][1]][1:]
            out('({}')
            out(f"(= {iterid} 0)")
            structlabel = newid('struct')
            out(f"(= {structlabel} {args[1][0]})")
            for i in range(len(props)):
                curvars = oldcurvars.copy()
                toki = oldtoki
                p = props[i][0]
                curvars[iterid] = getstructproptype(args[1][1], p)
                out(f"(= {iterid} (!! {structlabel} {getstructpropoffset(args[1][1], p)} 8))")
                expr()
            outrp()
            outrp()
            return types[voidkey]
        elif len(args) == 3 and isstruct(args[2][1]) and structhastrait(args[2][1], trait):
            name = 'len'
            offset = getstructpropoffset(args[2][1], name) 
            t = getstructproptype(args[2][1], name)
            eachid = args[1][0] 
            iterid = args[0][0]#newid('iter') 
            out(f"(= {iterid} 0) (= {maxid} (!! {s} {offset} 8)) (= {stepid} 1)")
            pushout()
            out(f'(= {eachid}' + '({}')
            targs = [args[2][1], types[intkey]]
            compilefunc(trait, targs, at=getstructtrait(args[2][1], trait)[1])
            mf = manglefunc(trait, targs)
            out(f"({mf} {args[2][0]} {iterid})")
            outrp()
            outrp()
            t = getfunctype(trait, targs)
            curvars[eachid] = t
            eachassign = popout()
        elif len(args) == 2 : out(f'(= {iterid} 0) (= {maxid} {args[1][0]}) (= {stepid} 1)')
        elif len(args) == 3 : out(f'(= {iterid} {args[1][0]}) (= {maxid} {args[2][0]}) (= {stepid} 1)')
        elif len(args) == 4 : out(f'(= {iterid} {args[1][0]}) (= {maxid} {args[2][0]}) (= {stepid} {args[3][0]})')
        else : err('too many arguments for for loop')
        out(f'(?? (< {iterid} {maxid})')
        if eachassign : out(eachassign)
        expr()
        out(f'(= {iterid} (+ {iterid} {stepid}))')
        outrp()
        outrp()
    return types[voidkey]

def typemismatch(e, f):
    expect(typetotext(e), typetotext(f))

def doglo():
    g = getok()
    #if g in curvars:
    #    err(f"variable {g} is already declared local")
    match('=')
    pushout()
    t = expr()
    e = popout()
    if not g in glotypes:
        glotypes[g] = t
    elif glotypes[g] != t:
        typemismatch(glotypes[g], t)
    out('({}')
    drop(g, glotypes[g])
    out(f'(:= {g}')
    copy(e, t)
    outrp()
    outrp()
    return t

def doglobal(g):
    out(g)
    return glotypes[g]

def doargc():
    out('@argc')
    return types[intkey]

def doargv(): 
    out('@argv') 
    return types[memkey]

def doalloc():
    out(f'(@ {allocfunc}')
    expr()
    outrp()
    return types[memkey]

def dofree():
    out(f'(@ {freefunc}')
    expr()    
    outrp() 
    return types[voidkey] 
    
def dotypeassert(t):
    if not t in curvars:
        err(f"'{t}' is not a variable")
    getok()
    target = gettype()
    match(')')
    tt = curvars[t]
    if tt != target:
        typemismatch(target, tt)
    out(t)
    return tt

def doprefixop(op):
    pushout()
    at = expr()
    a = popout()
    pushout()
    bt = expr()
    b = popout()
    #if at != bt:
    #    typemismatch(at, bt)
    affirmcanop(op, at, bt)
    f = 'f' if at == types[fltkey] and op[0] != 'f' else ''
    rop = f'{f}{op}'
    out('({}')
    #olda = a
    #aid = newid('a')
    #out(f'(= {aid} {a})')
    #a = aid
    if a[0:3] == '(!!':
        #pa = a[:2] + ':' + a.rstrip()[3:-1]
        #out(f'{pa} {sop})')
        core = ''
        i = 3
        depth = 1
        while a[i] == ' ' : i += 1
        if a[i] == '(':
            core += '('
            i += 1
            while depth > 0:
                if a[i] == '(' : depth += 1
                elif a[i] == ')' : depth -= 1
                core += a[i]
                i += 1
        else:
            while a[i] != ' ':
                core += a[i]
                i += 1
        while a[i] == ' ' : i += 1
        ind = ''
        while a[i] != ' ':
            ind += a[i]
            i += 1
        core = core
        coreid = newid('core')
        out(f'(= {coreid} {core})')
        pushout()
        result = doop(rop, f'(!! {coreid} {ind} 8)', b, at, bt)
        sop = popout()
        out(f'(!: {coreid} {ind} 8 {sop})')        
    else:
        pushout()
        result = doop(rop, a, b, at, bt)
        sop = popout()
        if a.strip() in curvars:
            out(f"(= {a} {sop})")
        elif a.strip() in glotypes:
            out(f"(:= {a} {sop})")
    outrp()
    return at
        
def dobreak():
    out('(>-)')
    return types[voidkey]
        
def dodollar():
    return expr()

def donot():
    pushout()
    expr()
    s = popout()
    out(f"(? {s} 0 1)")
    return types[intkey]
        
def dofp():
    out('({}')
    name = getok()
    argnum = getfuncargs(name)
    typs = []
    for i in range(argnum):
        typs.append(gettype())
    compilefunc(name, typs)
    out(getfp(name, typs))
    outrp()
    return hashfp(name, typs)
    
def dofpexec():
    global toki
    oldtoki = toki
    pushout()
    out('(\\>')
    fpt = expr()
    s = popout()
    if not isfp(fpt):
        toki = oldtoki
        return doprefixop('*')
    out(s)
    argtypes = fpargs(fpt)
    for a in argtypes:
        t = expr()
        if a != t:
            typemismatch(a, t)
    outrp()
    return fpret(fpt)

def dostructtostr():
    pushout()
    t = expr()
    s = popout()
    out(f'(sys_struct{t}tostr {s})')
    return getfunctype('str', [])

def docase():
    out('({}')
    key = newid('casekey')
    out(f'(= {key}')
    t = expr()
    outrp()
    match(':')
    match('{')
    skipnl()
    def casesub():
        if toptok() == '_':
            getok()
            match(':')
            return expr()
        else:
            out('(?')
            pushout()
            ts = expr()
            s = popout()
            out('({}')
            compilefunc('equals', [t, ts])
            out(f"({manglefunc('equals', [t, ts])} {key} {s})")
            outrp()
            match(':')
            r = expr()
            skipnl()
            rb = casesub()
            outrp()
            if r == rb : return r
            else : return None
    t = casesub()
    if t == None : t = types[voidkey]
    outrp()
    skipnl()
    match('}')
    return t

def dopragma():
    global cargs
    if toptok() == 'C':
        getok()
        cargs += getok()[1:-1] + ' '

def donomangle():
    name = getok()
    args = []
    for i in range(getfuncargs(name)):
        args.append(gettype())
    compilefunc(name, args, isnomangle=True)

def doimport():
    name = getok()
    args = []
    rettype = types[voidkey]
    while toptok() not in ['\n', rettypekey]:
        args.append(gettype())
    if toptok() == rettypekey:
        getok()
        rettype = gettype()
    out(f"(<<> {name} ({' '.join([str(i) for i in range(len(args))])}))")
    setfuncargs(name, len(args))
    setfunctype(name, args, rettype)
    setdecfunctype(name, rettype)
    addimportedfunc(name)
    
def exprsub():
    t = getok()
    result = None
    pushout()
    if t == fnkey : result = dofunc()
    elif t == cfkey : result = docf()
    elif t == eqtypekey : result = doeqtype(t)
    elif t == haspropkey : result = doeqtype(t)
    elif t == weakcastkey : result = doweakcast()
    elif t == memindexkey : result = domemindex()
    elif t == memindexsetkey : result = domemindexset()
    elif t == sizeofkey : result = dosizeof()
    elif t == copykey : result = docopy()
    elif t == dropkey : result = dodrop()
    elif t == forkey : result = dofor()
    elif t == glokey : result = doglo()
    elif t == argckey : result = doargc()
    elif t == argvkey : result = doargv()
    elif t == allockey : result = doalloc()
    elif t == freekey : result = dofree()
    elif t == breakkey : result = dobreak()
    elif t == dollarkey : result = dodollar()
    elif t == notkey : result = donot()
    elif t == fpkey : result = dofp()
    elif t == fpexeckey : result = dofpexec()
    elif t == structtostrkey : result = dostructtostr()
    elif t == casekey : result = docase()
    elif t == pragmakey : result = dopragma()
    elif t == nomanglekey : result = donomangle()
    elif t == importkey : result = doimport()
    elif t in typekeys : result = dotypekey(t)
    elif t == '(' : result = doparens()
    elif t == '{' : result = doblock()
    elif t == ' [' or t == '[' : result = dosquarebrace()
    elif t == '_' : result = dounderscore()
    elif t == '|' : result = doguard()
    elif t[0] == '`' : result = docstr(t)
    elif t[0] == "'" : result = dochar(t)
    elif isint(t) : result = donum(t)
    elif t in ops : result = doprefixop(t)
    elif toptok() in ['=', iskey] : result = doassign(t)
    elif toptok() == '.(' : result = dotypeassert(t)
    elif t in curvars and curvars[t] != None : result = dovar(t)
    elif hasfunc(t) : result = docall(t)
    elif t in glotypes : result = doglobal(t)
    else : err(f"malformed expression '{t}'")
    s = popout()
    isdot = False
    isbrace = False
    while isstruct(result) and toptok() in ['.', '[']:
        if toptok() == '.':
            isdot = True
            isbrace = False
            pushout()
            getok()
            name = getok()
            offset = getstructpropoffset(result, name)
            result = getstructproptype(result, name)
            out(f"(!! {s} {offset} 8)")
            s = popout()
        elif toptok() == '[':
            isdot = False
            isbrace = True
            pushout()
            getok()
            it = expr()
            ind = popout()
            match(']')
            if toptok() == '=':
                getok()
                trait = '[]='
                if structhastrait(result, trait):
                    pushout()
                    at = expr()
                    a = popout()
                    out('({}')
                    args = [result, it, at]
                    compilefunc(trait, args, at=getstructtrait(result, trait)[1])
                    mf = manglefunc(trait, args)
                    out(f"({mf} {s} {ind} {a})")
                    outrp()
                    return getfunctype(trait, args)
                else:
                    err(f"cannot index type '{result}'")
            else:
                trait = '[]'
                if structhastrait(result, trait):
                    pushout()
                    out('({}')
                    args = [result, it]
                    compilefunc(trait, args, at=getstructtrait(result, trait)[1])
                    mf = manglefunc(trait, args)
                    out(f"({mf} {s} {ind})")
                    outrp()
                    result = getfunctype(trait, args)
                    s = popout()
                else:
                    err(f"cannot index type '{result}'")
    if isdot and toptok() == '=':
        getok()
        s = s[:2] + ':' + s[3:]
        s = s[:-2]
        out(s)
        pushout()
        e = expr()
        ae = popout()
        copy(ae, e)
        if e != result:
            expect(typetotext(result), typetotext(e))
        outrp()
    else : out(s)
    return result

def canop(op, a, b):
    if isstruct(a):
        return structhastrait(a, op)
    eligible = [types[chrkey], types[intkey], types[fltkey]]
    return a in eligible and b in eligible

def expr():
    pushout()
    result = exprsub()
    a = popout()
    while toptok() in ops or toptok() in boolops:
        pushout()
        op = getok()
        pushout() 
        r = exprsub()
        b = popout()
        result = doop(op, a, b, result, r)
        a = popout()
    out(a)
    return result

def affirmcanop(op, result, r):
    if not canop(op, result, r):
        err(f"cannot perform operation '{op}' on types '{result}' and '{r}'")
    
def doop(op, a, b, result, r):
        affirmcanop(op, result, r)
        if isstruct(result):
            out('({}')
            typs = [result, r]
            args = [a, b]
            compilefunc(op, typs, at=getstructtrait(result, op)[1])
            result = getfunctype(op, typs)
            out(f"({manglefunc(op, typs)} {a} {b})")
            outrp()
        elif op in boolops:
            if op == 'and':
                out(f"(? {a} (? {b} 1 0) 0)")
            elif op == 'or':
                out(f"(? {a} 1 (? {b} 1 0))")
            else:
                err('something went wrong')
            result = types[intkey]
        else:
            outlp()
            if (result == types[fltkey] or r == types[fltkey]) and op[0] != 'f' : out(f'f{op}')
            else : out(op)
            if result == types[fltkey] and r != types[fltkey]:
                out(a)
                out(f"(@ longtodub {b})")
            elif result != types[fltkey] and r == types[fltkey]:
                out(f"(@ longtodub {a})")
                out(b)
            else:
                out(a)
                out(b)
            if r == types[fltkey] : result = types[fltkey]
            elif result == types[intkey] and r == types[chrkey] : result = types[chrkey]
            outrp()
        return result
    
def findfuncs(dotypes=False):
    global toki
    toki = 0
    while not eof():
        if toptok() in [fnkey, importkey]:
            dofoundfn(dotypes=dotypes)
        getok() 
    toki = 0
            
def dofoundfn(dotypes=False):
            if toptok() == importkey:
                getok()
                doimport()
                return
            getok()
            name = getok()
            if name.strip() == '[' and toptok() == ']':
                name = '[]'
                getok()
            if name == '[]' and toptok() == '=':
                name = '[]='
                getok()
            funclocs[name] = toki
            argnum = 0
            args = []
            copyvars = []
            while toptok() not in [rettypekey, '=']:
                iscopy = toptok() == '^'
                if iscopy : getok()
                t = getok()
                args.append(t)
                if iscopy : copyvars.append(t)
                argnum += 1
            setfuncargs(name, argnum)
            if toptok() == rettypekey:
                if dotypes:
                    getok()
                    t = gettype()
                    setdecfunctype(name, t)
                else:
                    while toptok() != '=' : getok()
            match('=')
            vars = args[:]
            if toptok() == '{':
                depth = 1
                getok()
                lasttok = ''
                while depth > 0:
                    t = getok()
                    if toptok() == '{' : depth += 1
                    elif toptok() == '}' : depth -= 1
                    elif toptok() in ['=', iskey] and lasttok != glokey : vars.append(t)
                    elif toptok() == fnkey : dofoundfn()
                    lasttok = t
            else:
                lasttok = ''
                depth = 0
                while toptok() != '\n' or depth > 0:
                    t = getok()
                    if toptok() == '{' : depth += 1
                    elif toptok() == '}' : depth -= 1
                    elif toptok() in ['=', iskey] and lasttok != glokey : vars.append(t)
                    elif toptok() == fnkey : dofoundfn()
                    lasttok = t
            funcvars[name] = vars
            funccopyvars[name] = copyvars

def findglos():
    global toki
    global glos
    glos = [] 
    toki = 0
    while not eof():
        if toptok() == glokey:
            getok()
            glos.append(toptok())
        getok()
    toki = 0

def scify(tokens):
    return [';' if t == '\n' else t for t in tokens]

def douses(used=[]):
    global tokens
    global toki
    toki = 0
    founduse = False
    newtokens = []
    while not eof():
        if toptok() == usekey:
            getok()
            if toptok()[0] == '"':
                founduse = True
                filelink = getok()[1:-1]
                if not filelink in used:
                    used.append(filelink)
                    newtokens += scify(tokenize(open(filelink).read()))
            else:
                newtokens.append(usekey)
        elif toptok() == pragmakey:
            while toptok() != '\n':
                if toptok()[0] == '"':
                    newtokens.append(f'`{toptok()[1:-1]}`')
                else:
                    newtokens.append(tokens[toki])
                getok()
        newtokens.append(tokens[toki])
        getok()
    newtokens.append(';')
    newtokens.append(';')
    toki = 0
    tokens = newtokens
    if founduse:
        douses(used=used)

def expandfstrs():
    global toki
    global tokens
    toki = 0
    newtokens = []
    while not eof():
        if toptok()[:2] == '$"':
            s = toptok()[2:-1]
            newt = []
            escape = False
            f = '"'
            e = ''
            for i in range(len(s)):
                c = s[i]
                if escape:
                    if c == '}':
                        escape = False
                        t = tokenize(e)
                        while t[0] == '\n' : t.pop(0)
                        while t[-1] == '\n' : t.pop()
                        newt += ['('] + t + [')']
                        e = ''
                    else : e += c
                elif c == '{':
                    if len(f) > 0 and f[-1] == '\\':
                        f.pop()
                        f += c
                    else:
                        f += '{}'
                        newt += ['%']
                        escape = True
                else:
                    f += c
            r = ['{', '(', f + '"'] + newt + [')', '}']
            newtokens += r
        else : newtokens.append(tokens[toki])
        getok()
    newtokens.append(';')
    newtokens.append(';')
    toki = 0
    tokens = newtokens

def expandstrs():
    global toki
    global tokens
    toki = 0
    newtokens = []
    while not eof():
        if toptok()[0] == '"':
            s = toptok()[1:-1]
            tmpvar = f'__RESERVED_9876543567897654567{toki}_'
            newtokens += ['(', '{', tmpvar, '=', 'vec', 'chr', ';']
            escape = False
            for c in s:
                if escape:
                    newtokens += ['vpush', tmpvar, 'weakcast', 'chr', str(escmap[c] if c in escmap else ord(c)), ';']
                    escape = False
                elif c == '\\':
                    escape = True
                else:
                    newtokens += ['vpush', tmpvar, f"'{c}'", ';']
            newtokens += [tmpvar, '}', ')']
        else : newtokens.append(tokens[toki])
        getok() 
    newtokens.append(';')
    newtokens.append(';')
    toki = 0 
    tokens = newtokens

def flatten(l):
    flat_list = [item for sublist in l for item in sublist]
    return flat_list

def expandlambdas():
    global toki
    global tokens
    toki = 0
    newtoks = []
    while not eof():
        if toptok() == lambdakey:
            getok()
            args = []
            typs = []
            rettype = None
            while toptok() not in ['=', rettypekey]:
                args.append(tokens[toki])
                getok()
                match('.(')
                t = []
                depth = 1
                while depth > 0:
                    if toptok() == '(' : depth += 1
                    elif toptok() == ')' : depth -= 1
                    t.append(tokens[toki])
                    getok()
                t.pop()
                typs.append(t)
            if toptok() == rettypekey:
                getok()
                rettype = gettype()
            getok()
            if toptok() == '{':
                getok()
                body = ['{']
                depth = 1
                while depth > 0:
                    if toptok() == '{' : depth += 1
                    elif toptok() == '}' : depth -= 1
                    body.append(tokens[toki])
                    getok()
            else:
                body = []
                while toptok() != '\n':
                    body.append(tokens[toki])
                    getok()
            name = newid('lambda')
            if rettype != None:
                setdecfunctype(name, rettype)
            fp = [fpkey, name] + flatten(typs)
            func = [fnkey, name] + args + ['='] + body
            expandedlambda = ['{'] + func + [';'] + fp + ['}']
            for t in expandedlambda : newtoks.append(t)
        else:
            newtoks.append(tokens[toki])
            getok()
    tokens = newtoks
    toki = 0

def blockifyfuncs():
    global toki
    global tokens
    toki = 0
    newtoks = []
    unblockedfound = False
    while not eof():
        if toptok() == 'fn':
            newtoks.append(getok())
            name = toptok()
            newtoks.append(name)
            getok()
            if name == ' [' and toptok() == ']':
                newtoks.append(']')
                getok()
                if toptok() == '=':
                    newtoks.append('=')
                    getok()
            while toptok() != '=':
                newtoks.append(tokens[toki])
                getok()
            newtoks.append('=')
            getok()
            if toptok() != '{':
                unblockedfound = True
                newtoks.append('{')
                depth = 0
                try:
                    while depth > 0 or toptok() != '\n':
                        if toptok() == '{' : depth += 1
                        elif toptok() == '}' : depth -= 1
                        elif toptok() == ' [' : depth += 1
                        elif toptok() == '[' : depth += 1
                        elif toptok() == ']' : depth -= 1
                        newtoks.append(tokens[toki])
                        getok()
                    newtoks += [';', '}', ';']
                except:
                    print(' '.join(tokens).replace(';', '\n'))
                    print('bad')
                    sys.exit(1)
        else:
            newtoks.append(tokens[toki])
            getok()
    tokens = newtoks
    toki = 0
    #print(' '.join(tokens).replace(';', '\n'))
    if unblockedfound : blockifyfuncs()

def onetokexp(isnoboundscheck):
    global toki
    global tokens
    toki = 0
    newtoks = []
    replace = {
        vgetkey : 'vqget' if isnoboundscheck else 'vget',
        vsetkey : 'vqset' if isnoboundscheck else 'vset',
    }
    while not eof():
        t = tokens[toki]
        if t in replace : t = replace[t]
        newtoks.append(t)
        getok()
    tokens = newtoks
    toki = 0

cargs = ''
def start(srcname, optimize=False, ismakeobject=False, isnoboundscheck=False):
    global tokens
    global cargs
    cargs = ''
    if not optimize : usecmalloc()
    src = open(srcname).read()
    tokens = ['use', '"hp"', ';'] + tokenize(src)
    douses()
    onetokexp(isnoboundscheck)
    expandfstrs()
    expandstrs()
    expandlambdas()
    blockifyfuncs()
    findfuncs(dotypes=False)
    findglos()
    findfuncs(dotypes=True)
    for g in glos:
        out(f'(:= {g} 0)')
    bodyname = 'ueibwbuinj98497656@@@@@@'
    outlp()
    out('<>')
    out(bodyname)
    out('()')
    pushout()
    while not eof():
        skipnl()
        expr()
        match('\n')
        skipnl()
    s = popout()
    for d in todrop:
        out(f"(= {d} 0)")
    out(s)
    outrp()
    out(f"({bodyname})")
    with open('hpout.seir', 'w') as f:
        f.write(output)
    objectstr = '-c' if ismakeobject else ''
    command = f"cat ./hpout.seir | ./seir {objectstr}"
    if optimize : command = f"cat ./hpout.seir | ./seirc {objectstr}"
    #print(output)
    subprocess.Popen(command, shell=True).wait()
    return {
        'cargs' : cargs
    }

#start()