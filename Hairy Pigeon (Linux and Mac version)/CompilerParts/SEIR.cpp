// clang++ -O3 SEIRMC.cpp -o seirmc

#include <iostream>
#include <fstream>
#include <streambuf>
#include <vector>
#include <regex>
#include <locale>
#include <stack>
#include <map>
#include <sstream>
#include <iomanip>

#include "format.cpp"

bool islinux = false;

bool ismakeobject = false;

string output = "";
string dataoutput = "tmp dq 0\n";
string curfunc = "top level scope";

vector<string> tokens;
 
string getcurfuncname() {
    return curfunc;
}
 
vector<string> refindall(string rs, string str) {
    vector<string> result;
    regex exp(rs);
    smatch res;
    while (regex_search(str, res, exp)) {
        result.push_back(res[0]);
        str = res.suffix();
    }
    return result;
}
 
template <typename T>
int vecindex(vector<T>& Names, T old_name_) {
    return find(Names.begin(), Names.end(), old_name_) - Names.begin();
}
 
template <typename T>
bool veccontains(vector<T> &v, T x) {
    return std::find(v.begin(), v.end(), x) != v.end();
}
 
template <typename T, typename U>
bool mapcontainskey(std::map<T, U>& m, T e) {
    auto it = m.find(e);
    return it != m.end();
}
 
template <typename T, typename U>
vector<T> getkeys(map<T, U>& m) {
    vector<T> v;
    for(auto it = m.begin(); it != m.end(); ++it) {
      v.push_back(it->first);
    }
    return v;
}

template <typename T>
vector<T> reversevec(vector<T>& v) {
    vector<T> result;
    for (int i = v.size() - 1; i >= 0; i--) {
        result.push_back(v.at(i));
    }
    return result;
}
 
bool isupper(const std::string& s) {
    return std::all_of(s.begin(), s.end(), [](unsigned char c){ return std::isupper(c); });
}
 
bool isnumber(const std::string& s) {
    if (s.size() == 0) return false;
    std::string::const_iterator it = s.begin();
    while (it != s.end() && std::isdigit(*it)) ++it;
    return !s.empty() && it == s.end();
}
 
bool isint(string s) {
    return isnumber(s) || (s.size() >= 3 && s.at(0) == '\'');
}

bool isFloat( string myString ) {
    std::istringstream iss(myString);
    float f;
    iss >> noskipws >> f; // noskipws considers leading whitespace invalid
    // Check the entire string was consumed and if either failbit or badbit is set
    return iss.eof() && !iss.fail(); 
}

std::string hexStr(unsigned char* data, int len)
{
    std::stringstream ss;
    ss << std::hex;
    for(int i=0;i<len;++i)
        ss << std::setw(2) << std::setfill('0') << (int)data[i];
    return ss.str();
}
 
bool isalnum(string& s) {
    if (isnumber(s)) return false;
    for (auto c : s) if (!isalnum(c)) return false;
    return true;
}

template<typename... Args>
void err(string s, Args... args);
void err(string s);
 
int chartoint(string& s) {
    return (int)s.at(1);
}
 
int toint(string s) {
    if (isnumber(s)) return stoi(s);
    if (s.size() >= 3 && s.at(0) == '\'') return chartoint(s);
    err("cannot convert '{}' to int", s);
    return 0;
}
 
//do not make this a reference
string makealnum(string s) {
    auto my_predicate = [](char c) -> bool {return !isalnum(c);};
    s.erase(std::remove_if(s.begin(), s.end(), my_predicate), s.end());
    return s;
}
 
int labeli = 0;
string uniqueid(string& s) {
    return format("@{}_{}", makealnum(s), labeli++);
}

string newname(string s) {return uniqueid(s);}
 
int ln;
void resetln() {
    ln = 0;
}
 
bool isonlychar(string& s, char c) {
    for (char d : s) {
        if (d != c) return false;
    }
    return true;
}

string readfile(string name) {
    std::ifstream t(name);
    std::string str((std::istreambuf_iterator<char>(t)),
                 std::istreambuf_iterator<char>());
    return str;
}

void writefile (string name, string& text) {
    ofstream myfile;
    myfile.open(name);
    myfile << text;
    myfile.close();
}

void out(string s) {
    output += s;
    output += '\n';
}

template<typename... Args>
void out(string s, Args... args) {
    out(format(s, args...));
}

void dataout(string s) {
    dataoutput += s;
    dataoutput += '\n';
}

template<typename... Args>
void dataout(string s, Args... args) {
    dataout(format(s, args...));
} 
 
void outrp() {
    out(")");
} 
 
void outlabel(string s) {
    output += s + ":\n";
} 
 
vector<string> outstk;
void pushout() {
    outstk.push_back(output);
    output = "";
} 
 
string popout() {
    auto result = output;
    try {
        output = outstk.at(outstk.size() - 1);
    } catch(...) {
        err("could not pop output");
    }
    outstk.pop_back();
    return result;
} 
 
bool docomments = false;
template<typename... Args>
void outcom(string s, Args... args) {
    if(docomments) out(format(";" + s, args...));
} 
 
string getcurfuncname();
string gettok();

void err(string s) {
    string t = "";
    for (int i = 0; i < 10; i++) {
        t += gettok() + " ";
    }
    cerr << "Error at line " << ln << " in " << getcurfuncname() << ": " << s << endl
    << t << endl;
    //printtokens();
    exit(EXIT_FAILURE);
}

template<typename... Args>
void err(string s, Args... args) {
    err(format(s, args...));
}

string toptok();
string rawtoptok();

string gettok() {
    try {
        auto t = rawtoptok();
        tokens.pop_back();
        if (t.at(0) == '\n') {
            ln++;
        }
        if (t == ";") return "\n ";
        if (t == ";;") return "\n";
        return t;
    } catch (...) {
        err("unexpected EOF");
    }
    return "";
}

string tokat(int i) {
    string s = "";
    try {
        s = tokens.at(tokens.size() - i - 1);
    } catch (...) {
        err("unexpected EOF");
    }
    return s;
}

string rawtoptok() {
    return tokat(0);
}

string toptok() {
    auto r = rawtoptok();
    auto s = gettok();
    if (r.at(0) == '\n') ln--;
    tokens.push_back(r);
    return s;
}

void expect(string e, string f) {
    err(format("expected '{}' found '{}'", e, f));
}

void match(string s) {
    auto t = gettok();
    if (s != t) expect(s, t);
}

void matchendline() {
    auto r = rawtoptok();
    auto t = gettok();
    if (t.at(0) != '\n' && t != ";") expect("end of line", t);
    if (t == "\n") {
        tokens.push_back(r);
        if (r.at(0) == '\n') ln--;
    }
}

void skipnl() {
    while(toptok().at(0) == '\n' && toptok() != "\n") gettok();
}

string getint() {
    auto t = gettok();
    if (!isint(t))
        expect("int", t);
    return t;
}

string getalnum() {
    auto t = gettok();
    if (!isalnum(t))
        expect("identifier", t);
    return t;
}

vector<string> tokenize(string s) {
    auto regex = R"(;[^\n]*|\(|\)|\"[^\"]*\"|[^\s\(\)]+)";
    auto toks = refindall(regex, s);
    vector<string> result;
    result.push_back("\n");
    for (auto s : reversevec(toks)) {
        if (s.at(0) != ';') {
            result.push_back(s);
        }
    }
    //result.push_back("\n");
    return result;
}

vector<string> stk;

void push(string s) {
    stk.push_back(s);
    out("push qword {}", s);
}

void pop(string s) {
    if (stk.size() == 0)
        err("attempt to pop from empty stack");
    stk.pop_back();
    out("pop {}", s);
}

void popnone() {
    if (stk.size() == 0) 
        err("attempt to pop from empty stack");
    stk.pop_back(); 
    out("add rsp, 8");
}

void resetstk(vector<string>& oldstk) {
    auto n = (stk.size()) - (oldstk.size());
    if (n) out("add rsp, {}", (n * 8));
    stk = oldstk;
}

void resetstkval(vector<string>& oldstk) {
    pop("rax");
    resetstk(oldstk);
    push("rax");
}

map<string, string> ops;
map<string, string> cmpops;
map<string, string> divops;
map<string, function<int(int, int)>> opfs;
map<string, string> fltops;
map<string, string> sizemap;
map<string, string> funclabels;
map<string, vector<string>> funcs;
map<string, string> globals;
vector<string> funcargs;

void expr();

/*
def rethere():
    out('add rsp, {}'.format(len(stk) * 8))
    out('ret')
*/

void rethere() {
    out("add rsp, {}", stk.size() * 8);
    out("ret");
}

/*
def dofunc():
    global funcargs
    global stk
    global curfunc
    oldfuncargs = funcargs
    oldstk = stk[:]
 
    stk = []
 
    skip = newname('skip')
    out('jmp {}'.format(skip))
    gettok()
    name = gettok()
    curfunc = name
    outlabel(funclabels[name])
    match("(")
    args = []
    while toptok() != ')':
        args.append(gettok())
    funcargs = args
    gettok()
    while toptok() != ')':
        expr()
        #if toptok() != ')' : popnone()
    pop('rax')
    rethere()
    outlabel(skip)

    funcargs = oldfuncargs
    stk = oldstk

    out('mov rax, {}'.format(funclabels[name]))
    push('rax')
*/
void dofuncsub(bool ispublic) {
    auto oldfuncargs = funcargs;
    auto oldstk = stk;
    stk = vector<string>();
    auto skip = newname("skip");
    out("jmp {}", skip);
    gettok();
    auto name = gettok();
    curfunc = name;
    if (ispublic) {
        out("global {}", funclabels.at(name));
        out("global _{}", name);
        out("_{}:", name);
    }
    outlabel(funclabels.at(name));
    match("(");
    vector<string> args;
    while (toptok() != ")") args.push_back(gettok());
    funcargs = args;
    gettok();
    while (toptok() != ")") expr();
    pop("rax");
    rethere();
    outlabel(skip);
    funcargs = oldfuncargs;
    stk = oldstk;
    out("mov rax, {}", funclabels.at(name));
    push("rax");
}

void dofunc() {
    dofuncsub(false);
}

void dopublicfunc() {
    dofuncsub(true);
}

void docall() {
    auto name = gettok();
    auto fargs = funcs.at(name);
    auto i = 0;
    while (toptok() != ")") {
        expr();
        i += 1;
    }
    if (i != fargs.size()) {
        err("bad number of arguments for '{}' expected '{}' found '{}'", name, fargs.size(), i);
    }
    out("call {}", (funclabels.at(name)));
    out("add rsp, {}", (i * 8));
    for (int j = 0; j < i; j++) stk.pop_back();
    push("rax");
}

void doexeclambda() {
    //auto name = gettok();
    //auto fargs = funcs.at(name);
    gettok();
    auto i = 0;
    do {
        expr();
        i += 1;
    } while (toptok() != ")");
    //if (i != fargs.size()) {
    //    err("bad number of arguments for '{}' expected '{}' found '{}'", name, fargs.size(), i);
    //}
    out("mov rax, [rsp + {}]", (i - 1) * 8);
    out("call rax");
    out("add rsp, {}", (i * 8));
    for (int j = 0; j < i; j++) stk.pop_back();
    push("rax");
}

void doarg() {
    auto s = gettok();
    push(format("[rsp + {}]", (stk.size() + 1 + (funcargs.size() - vecindex(funcargs, s) - 1)) * 8));
}

void doint() {
    push(gettok());
}

void doflt() {
    out("mov rax, {}", gettok());
    push("rax");
}

void doop() {
    auto op = gettok();
    if (isint(toptok())) {
        auto a = gettok();
        if (isint(toptok())) {
            push(to_string(opfs.at(op)(toint(a), toint(gettok()))));
        } else {
            expr();
            out("mov rax, {}", toint(a));
            pop("rbx");
            out("{} rax, rbx", (ops.at(op)));
            push("rax");
        }
    } else {
        expr();
        if (isint(toptok())) {
            pop("rax");
            out("{} rax, {}", ops[op], gettok());
            push("rax");
        } else {
            expr();
            pop("rbx");
            pop("rax");
            out("{} rax, rbx", (ops[op]));
            push("rax");
        }
    }
}

void dofltop(){
    auto op = gettok();
    expr();
    expr();
    pop("rbx");
    pop("rax");
    out("movq xmm0, rax");
    out("movq xmm1, rbx");
    out("{}sd xmm0, xmm1", fltops[op]);
    out("movq rax, xmm0");
    push("rax");
}

void docmpop(){
    auto op = gettok();
    expr();
    expr();
    out("xor rax, rax");
    pop("rbx");
    pop("rcx");
    out("cmp rcx, rbx");
    out("{} al", (cmpops.at(op)));
    push("rax");
}
 
void dodivop() {
    auto op = gettok();
    expr();
    expr();
    pop("rbx");
    pop("rax");
    out("xor rdx, rdx");
    out("idiv rbx");
    push(divops.at(op));
}

void doprintf() {
    gettok();
    expr();
    expr();
    pop("rcx");
    pop("rbx");
    out("printf rbx, rcx");
    push("rbx");
}

/*
def dostr(israw=False):
    s = gettok()
    name = newname('rawstr')
    escape = False
    vals = []
    escmap = {'n' : 10, 't' : 9, '0' : 0}
    for c in s[1:-1]:
        if escape:
            if c in escmap : vals.append(str(escmap[c]))
            else : vals.append(str(ord(c)))
            escape = False
        elif c == '\\' and not israw : escape = True
        else : vals.append(str(ord(c)))
    ds = ', '.join(vals)
    if s[1:-1] : dataout('{} db {}, 0'.format(name, ds))
    else : dataout('{} db 0'.format(name))
    out('mov rax, {}'.format(name))
    push('rax')
*/

void dostr(bool israw=false) {
    auto s = gettok();
    auto name = newname("str");
    auto escape = false;
    vector<string> vals;
    map<char, int> escmap;
    escmap['n'] = 10;
    escmap['t'] = 9;
    escmap['0'] = 0;
    for (int i = 1; i < s.size() - 1; i++) {
        char c = s.at(i);
        if (escape) {
            if (mapcontainskey(escmap, c)) vals.push_back(to_string(escmap.at(c)));
            else vals.push_back(to_string((int)c));
            escape = false;
        } else if (c == '\\' && !israw) escape = true;
        else vals.push_back(to_string((int)c));
    }
    string ds = "";
    for (auto v : vals) {
        ds += v + ", ";
    }
    ds.resize(ds.size() - 2);
    if (s.size() > 2) dataout("{} db {}, 0", name, ds);
    else dataout("{} db 0", name);
    out("mov rax, {}", name);
    push("rax");
}

/*
def doif():
    global stk
    gettok()
 
    out(';if')
 
    elsel = newname('else')
    endl = newname('endif')
 
    oldstk = stk[:]
    expr()
    resetstkval(oldstk)
    pop('rax')
    out('test rax, rax')
    out('je {}'.format(elsel))
    expr()
    resetstkval(oldstk)
    #pop('rax')

    out('jmp {}'.format(endl))
    stk = oldstk[:]
    outlabel(elsel)
    expr()
    resetstkval(oldstk)
    #pop('rax') 
    outlabel(endl)
*/

void doif() {
    gettok();
    auto elsel = newname("else");
    auto endl = newname("endif");
    auto oldstk = stk;
    expr();
    resetstkval(oldstk);
    pop("rax");
    out("test rax, rax");
    out("je {}", elsel);
    expr();
    resetstkval(oldstk);
    
    out("jmp {}", endl);
    stk = oldstk;
    outlabel(elsel);
    expr();
    resetstkval(oldstk);
    outlabel(endl);
}

vector<vector<string>> whilestks;
vector<string> whileexits;
void dowhile() {
    gettok();

    auto loop = newname("while");
    auto exit = newname("exitwhile");

    auto oldstk = stk;
    whilestks.push_back(oldstk);
    whileexits.push_back(exit);
    outlabel(loop);
    expr();
    resetstkval(oldstk);
    pop("rax");
    out("test rax, rax");
    out("je {}", (exit));
    while (toptok() != ")") expr();
    resetstk(oldstk);
    out("jmp {}", (loop));
    outlabel(exit);
    
    whilestks.pop_back();
    whileexits.pop_back();

    push("0");
}

void dobreak() {
    gettok();
    resetstk(whilestks.at(whilestks.size()-1));
    out("jmp {}", whileexits.at(whileexits.size()-1));
}

void doassign() {
    gettok();
    auto name = gettok();
    expr();
    if (!veccontains(stk, name)) {
        stk[stk.size()-1] = name;
    } else {
        out("mov rax, [rsp]");
        out("mov [rsp + {}], rax", (stk.size() - vecindex(stk, name) - 1) * 8);
    }
}

void dovar() {
    auto s = gettok();
    push(format("[rsp + {}]", (stk.size() - vecindex(stk, s) - 1) * 8));
}

void doglobalassign() {
    gettok();
    auto name = gettok();
    expr();
    out("mov rax, [rsp]");
    out("mov rbx, {}", (globals[name]));
    out("mov [rbx], rax");
}

void doglobal() {
    auto name = gettok();
    out("mov rax, {}", (globals[name]));
    out("mov rax, [rax]");
    push("rax");
}

void doblock() {
    gettok();
    auto oldstk = stk;
    if (toptok() == ")") {
        push("0");
        return;
    }
    while (toptok() != ")")
        expr();
    resetstkval(oldstk);
}

void docfunc() {
    gettok();
    auto name = gettok();
    vector<string> regs = {"r9", "r8", "rcx", "rdx", "rsi", "rdi"}; //['rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9'][::-1];
    while (toptok() != ")") {
        if (regs.size() <= 0) {
            err("too many args for cfunc");
        }
        auto r = regs.at(regs.size() - 1);
        regs.pop_back();
        expr();
        pop(r);
    }
    auto pref = islinux ? "" : "_";
    auto s = format("\n\
    mov r15, rsp\n\
    and r15, 15\n\
    sub rsp, r15\n\
    push r15\n\
    push 0\n\
    mov rbp, rsp\n\
    push 0\n\
    push 0\n\
    push 0\n\
    push 0\n\
    xor rax, rax\n\
    extern {}\n\
    call {}\n\
    add rsp, 40\n\
    pop r15\n\
    add rsp, r15\n\
    ", pref + name, pref + name);
    out(s);
    push("rax");
}

void domalloc() {
    gettok();
    expr();
    pop("rax");
    out("malloc rax");
    push("rax");
}

void dofree() { 
    gettok(); 
    expr(); 
    pop("rax");
    out("free rax");
    push("rax");
}

void doarrayassign() {
    gettok();
    expr();
    expr();
    auto size = getint();
    expr();
    pop("rax");
    pop("rbx");
    pop("rcx");
    out("mov [rcx + rbx * {}], {}", size, sizemap.at(size));
    push("rcx");
}
 
void doarrayindex() {
    gettok();
    expr();
    expr();
    auto size = getint();
    pop("rbx");
    pop("rcx");
    out("xor rax, rax");
    out("mov {}, [rcx + rbx * {}]", sizemap.at(size), size);
    push("rax");
}

void doret() {
    gettok();
    expr();
    pop("rax");
    rethere();
}

void sexpr(){
    gettok();
    auto t = toptok();
    if (mapcontainskey(ops, t)) doop();
    else if (mapcontainskey(cmpops, t)) docmpop();
    else if (mapcontainskey(divops, t)) dodivop();
    else if (mapcontainskey(fltops, t)) dofltop();
    else if (toptok() == "<>") dofunc();
    else if (toptok() == "<>>") dopublicfunc();
    else if (toptok() == "?") doif();
    else if (toptok() == "??") dowhile();
    else if (toptok() == "=") doassign();
    else if (toptok() == ":=") doglobalassign();
    else if (toptok() == "!!") doarrayindex();
    else if (toptok() == "!:") doarrayassign();
    else if (toptok() == "{}") doblock();
    else if (toptok() == "@") docfunc();
    //else if (toptok() == "><") doret();
    else if (toptok() == ">-") dobreak();
    else if (toptok() == "\\>") doexeclambda();
    else if (mapcontainskey(funcs, t)) docall();
    else err("malformed s expression '{}'", t);
    match(")");
}

void expr(){
    auto t = toptok();
    if (t == "(") sexpr();
    else if (isint(t)) doint();
    else if (isFloat(t)) doflt();
    else if (veccontains(stk, t)) dovar();
    else if (veccontains(funcargs, t)) doarg();
    else if (mapcontainskey(globals, t)) doglobal();
    else if (t.at(0) == '"') dostr();
    else err("malformed expression '{}'", t);
}

void findfuncs() {
    auto oldtokens = tokens;
    while (tokens.size() > 1) {
        auto s = gettok();
        if (s == "<>" || s == "<>>") {
            auto name = gettok();
            match("(");
            vector<string> args;
            while (toptok() != ")") {
                args.push_back(gettok());
            }
            funclabels[name] = newname(name);
            funcs[name] = args;
        } else if (s == ":=") {
            auto name = gettok();
            globals[name] = newname(name);
            dataout("{} dq 0", globals[name]);
        }
    }
    tokens = oldtokens;
}

void start(string src){
    tokens = tokenize(src);
    findfuncs();
    if (!ismakeobject) {
        out("global _main");
        outlabel("_main");
    }
    auto name = "@argc";                                                                              
    globals[name] = newname(name);                                                                      
    dataout("{} dq 0", globals[name]);
    out("mov rax, {}", globals[name]);
    out("mov [rax], rdi");
    name = "@argv";               
    globals[name] = newname(name);     
    dataout("{} dq 0", globals[name]); 
    out("mov rax, {}", globals[name]); 
    out("mov [rax], rsi");
    while (tokens.size() > 1) {
        expr();
        popnone();
    }
    vector<string> v;
    resetstk(v);
    out("ret");
    //cout << output << endl;
    auto asmmacros = readfile("asmmacros.txt");
    auto result = asmmacros + "\nsection .data\n" + dataoutput + "\nsection .text\n" + output;
    writefile("rout.asm", result);
    //system("nasm -fmacho64 rout.asm && clang -Wl,-no_pie file.o rout.o 2>&1 | ./removewarnings");
}

int main(int argc, char ** argv) {
    /*
    if (argc < 2) {
        err("bad number of arguments");
    }
    */

    for (int i = 0; i < argc; i++) {
        string s = argv[i];
        if (s == "-c") ismakeobject = true;
    }
    
    ops["+"] = "add";
    ops["-"] = "sub";
    ops["*"] = "imul";
    ops["^"] = "xor";
    ops["|"] = "or";
    ops["&"] = "and";
    
    cmpops["=="] = "sete";
    cmpops["!="] = "setne";
    cmpops["<"] = "setl";
    cmpops["<="] = "setle";
    cmpops[">"] = "setg";
    cmpops[">="] = "setge";

    divops["/"] = "rax";
    divops["%"] = "rdx";
    
    opfs["+"] = [](int a, int b)->int{return a + b;};
    opfs["-"] = [](int a, int b)->int{return a - b;};
    opfs["*"] = [](int a, int b)->int{return a * b;};
    opfs["/"] = [](int a, int b)->int{return a / b;};
    opfs["&"] = [](int a, int b)->int{return a & b;};
    opfs["|"] = [](int a, int b)->int{return a | b;};
    opfs["^"] = [](int a, int b)->int{return a ^ b;};
    
    fltops["f+"] = "add";
    fltops["f-"] = "sub";
    fltops["f*"] = "mul";
    fltops["f/"] = "div";
    
    sizemap["1"] = "al";
    sizemap["2"] = "ax";
    sizemap["4"] = "eax";
    sizemap["8"] = "rax";
    
    string src = "";
    for (std::string line; std::getline(std::cin, line);) {
        src += line + "\n";
    }
    src += "(@ exit 0)";
    start(src);
    
    return 0;
}

