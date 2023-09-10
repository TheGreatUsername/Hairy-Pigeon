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
#include <functional>

#include "format.hpp"

bool islinux = false;

bool ismakeobject = false;

using namespace std;

std::string output = "";
std::string dataoutput = "";
std::string curfunc = "top level scope";

std::vector<std::string> tokens;
 
std::string getcurfuncname() {
    return curfunc;
}
 
std::vector<std::string> refindall(std::string rs, std::string str) {
    std::vector<std::string> result;
    regex exp(rs);
    smatch res;
    while (regex_search(str, res, exp)) {
        result.push_back(res[0]);
        str = res.suffix();
    }
    return result;
}
 
template <typename T>
int vecindex(std::vector<T>& Names, T old_name_) {
    return find(Names.begin(), Names.end(), old_name_) - Names.begin();
}
 
template <typename T>
bool veccontains(std::vector<T> &v, T x) {
    return std::find(v.begin(), v.end(), x) != v.end();
}
 
template <typename T, typename U>
bool mapcontainskey(std::map<T, U>& m, T e) {
    auto it = m.find(e);
    return it != m.end();
}
 
template <typename T, typename U>
std::vector<T> getkeys(map<T, U>& m) {
    std::vector<T> v;
    for(auto it = m.begin(); it != m.end(); ++it) {
      v.push_back(it->first);
    }
    return v;
}

template <typename T>
std::vector<T> reversevec(std::vector<T>& v) {
    std::vector<T> result;
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
    auto it = std::find_if(s.begin(), s.end(), std::not_fn(&::isdigit));
    return !s.empty() && it == s.end();
}
 
bool isint(string s) {
    return isnumber(s) || (s.size() >= 3 && s.at(0) == '\'') || s[0] == '0' && s[1] == 'x';
}

bool isFloat( std::string mystring ) {
    std::stringstream iss(mystring);
    float f;
    iss >> noskipws >> f; // noskipws considers leading whitespace invalid
    // Check the entire std::string was consumed and if either failbit or badbit is set
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
 
bool isalnum(std::string& s) {
    if (isnumber(s)) return false;
    for (auto c : s) if (!isalnum(c)) return false;
    return true;
}

template<typename... Args>
void err(std::string s, Args... args);
void err(std::string s);
 
int chartoint(std::string& s) {
    return (int)s.at(1);
}
 
int toint(std::string s) {
    if (isnumber(s)) return stoi(s);
    if (s.size() >= 3 && s.at(0) == '\'') return chartoint(s);
    err("cannot convert '{}' to int", s);
    return 0;
}
 
//do not make this a reference
std::string makealnum(std::string s) {
    auto my_predicate = [](char c) -> bool {return !isalnum(c);};
    s.erase(std::remove_if(s.begin(), s.end(), my_predicate), s.end());
    return s;
}

std::string charhash(char c) {
    return format("_chr_{}_", (int)c);
}

std::string cifylabel(std::string s) {
    std::string result = "";
    for (auto c : s) {
        if (!isalnum(c)) {
            result += charhash(c);
        } else {
            result += c;
        }
    }
    return result;
}
 
int labeli = 0;
std::string uniqueid(std::string& s) {
    return cifylabel(format("@{}_{}", makealnum(s), labeli++));
}

std::string newname(std::string s) {return uniqueid(s);}
 
int ln;
void resetln() {
    ln = 0;
}
 
bool isonlychar(std::string& s, char c) {
    for (char d : s) {
        if (d != c) return false;
    }
    return true;
}

std::string readfile(std::string name) {
    std::ifstream t(name);
    std::string str((std::istreambuf_iterator<char>(t)),
                 std::istreambuf_iterator<char>());
    return str;
}

void writefile (std::string name, std::string& text) {
    ofstream myfile;
    myfile.open(name);
    myfile << text;
    myfile.close();
}

void out(std::string s) {
    output += s;
    output += '\n';
}

template<typename... Args>
void out(std::string s, Args... args) {
    out(format(s, args...));
}

void dataout(std::string s) {
    dataoutput += s;
    dataoutput += '\n';
}

template<typename... Args>
void dataout(std::string s, Args... args) {
    dataout(format(s, args...));
} 
 
void outrp() {
    out(")");
} 
 
void outlabel(std::string s) {
    output += s + ":\n";
} 
 
std::vector<std::string> outstk;
void pushout() {
    outstk.push_back(output);
    output = "";
} 
 
std::string popout() {
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
void outcom(std::string s, Args... args) {
    if(docomments) out(format(";" + s, args...));
} 
 
std::string getcurfuncname();
 
void err(std::string s) {
    cerr << "Error at line " << ln << " in " << getcurfuncname() << ": " << s << endl;
    //printtokens();
    exit(EXIT_FAILURE);
}

template<typename... Args>
void err(std::string s, Args... args) {
    err(format(s, args...));
}

std::string toptok();
std::string rawtoptok();

std::string gettok() {
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

std::string tokat(int i) {
    std::string s = "";
    try {
        s = tokens.at(tokens.size() - i - 1);
    } catch (...) {
        err("unexpected EOF");
    }
    return s;
}

std::string rawtoptok() {
    return tokat(0);
}

std::string toptok() {
    auto r = rawtoptok();
    auto s = gettok();
    if (r.at(0) == '\n') ln--;
    tokens.push_back(r);
    return s;
}

void expect(std::string e, std::string f) {
    err(format("expected '{}' found '{}'", e, f));
}

void match(std::string s) {
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

std::string getint() {
    auto t = gettok();
    if (!isint(t))
        expect("int", t);
    return t;
}

std::string getalnum() {
    auto t = gettok();
    if (!isalnum(t))
        expect("identifier", t);
    return t;
}

std::vector<std::string> tokenize(std::string s) {
    auto regex = R"(;[^\n]*|\(|\)|\"[^\"]*\"|[^\s\(\)]+)";
    auto toks = refindall(regex, s);
    std::vector<std::string> result;
    result.push_back("\n");
    for (auto s : reversevec(toks)) {
        if (s.at(0) != ';') {
            result.push_back(s);
        }
    }
    //result.push_back("\n");
    return result;
}

std::vector<std::string> stk;

void push(std::string s) {
    stk.push_back(s);
    out("push qword {}", s);
}

void pop(std::string s) {
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

void resetstk(std::vector<std::string>& oldstk) {
    auto n = (stk.size()) - (oldstk.size());
    if (n) out("add rsp, {}", (n * 8));
    stk = oldstk;
}

void resetstkval(std::vector<std::string>& oldstk) {
    pop("rax");
    resetstk(oldstk);
    push("rax");
}

map<std::string, std::string> ops;
map<std::string, std::string> cmpops;
map<std::string, std::string> divops;
map<std::string, function<int(int, int)>> opfs;
map<std::string, std::string> fltops;
map<std::string, std::string> sizemap;
map<std::string, std::string> funclabels;
map<std::string, std::vector<std::string>> funcs;
map<std::string, std::string> funcbodies;
map<std::string, std::string> globals;
std::vector<std::string> funcargs;
std::vector<std::string> curvars;
//std::vector<std::string> outstk;

// void pushout() {
//     outstk.push_back(output);
//     output = "";
// }

// std::string popout() {
//     if (outstk.size() < 1)
//         err("attempt to pop empty out stack");
//     auto result = outstk.at(outstk.size()-1);
//     outstk.pop_back();
//     return result;
// }

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
    pushout();
    auto oldfuncargs = funcargs;
    auto oldcurvars = curvars;
    curvars = std::vector<std::string>();
    gettok();
    auto name = gettok();
    curfunc = name;
    pushout();
    out("gt");
    out(funclabels.at(name));
    match("(");
    out("(");
    std::vector<std::string> args;
    while (toptok() != ")") {
        std::string arg = cifylabel(gettok());
        args.push_back(arg);
        curvars.push_back(arg);
        out("gt var_{}", arg);
        if (toptok() != ")") out(",");
    }
    funcargs = args;
    gettok();
    out(")");
    auto funcheader = popout();
    dataout("{};", funcheader);
    out(funcheader);
    out("{");
    pushout();
    out("return ({");
    while (toptok() != ")") {
        expr();
        out(";");
    }
    out("});}");
    auto retbody = popout();
    for (auto v : curvars) {
        if (!veccontains(args, cifylabel(v))) out("gt var_{} = 0;", cifylabel(v));
    }
    out(retbody);
    funcargs = oldfuncargs;
    curvars = oldcurvars;
    funcbodies[name] = popout();
    out("(gt){}", funclabels.at(name));
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
    out(funclabels.at(name));
    out("(");
    while (toptok() != ")") {
        expr();
        if (toptok() != ")") out(",");
        i += 1;
    }
    out(")");
    if (i != fargs.size()) {
        err("bad number of arguments for '{}' expected '{}' found '{}'", name, fargs.size(), i);
    }
}

void doexeclambda() {
    gettok();
    pushout();
    expr();
    auto f = popout();
    std::vector<std::string> args;
    while (toptok() != ")") {
        pushout();
        expr();
        auto e = popout();
        args.push_back(e);
    }
    out("((gt (*) (");
    for (int i = 0; i < args.size(); i++) {
        out("gt");
        if (i != args.size()-1) {
            out(",");
        }
    }
    out(")){})(", f);
    for (int i = 0; i < args.size(); i++) {
        auto a = args.at(i);
        out(a);
        if (i != args.size()-1) {
            out(",");
        }
    }
    out(")");
}

void doarg() {
    auto s = cifylabel(gettok());
    out(s);
}

void doint() {
    out(gettok());
}

void doflt() {
    // out("({");
    // out("double tmp = ");
    // out(gettok());
    // out(";");
    // out("*(gt*)&tmp;");
    // out("})");
    out(gettok());
}

void doop() {
    auto op = gettok();
    out(ops.at(op));
    out("(");
    expr();
    out(",");
    expr();
    out(")");
}

void dofltop(){
    auto op = gettok();
    out(fltops.at(op));
    out("(");
    expr();
    out(",");
    expr();
    out(")");
}

void docmpop(){
    auto op = gettok();
    out(cmpops.at(op));
    out("(");
    expr();
    out(",");
    expr();
    out(")");
}
 
void dodivop() {
    auto op = gettok();
    out(divops.at(op));
    out("(");
    expr();
    out(",");
    expr();
    out(")");
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
    out("((gt)(void*){})", s);
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
    out("(");
    expr();
    out("?");
    expr();
    out(":");
    expr();
    out(")");
}

std::vector<std::vector<std::string>> whilestks;
std::vector<std::string> whileexits;
void dowhile() {
    gettok();
    out("({ while (");
    expr();
    out(") {");
    while (toptok() != ")") {
        expr();
        out(";");
    }
    out("} 0;})");
}

void dobreak() {
    gettok();
    out("({break; 0;})");
}

void doassign() {
    gettok();
    auto name = gettok();
    out("(");
    if (!veccontains(curvars, name)) {
        curvars.push_back(name);
        //out("gt");
    }
    auto cname = cifylabel(name);
    out("var_{}", cname);
    out("= (gt)");
    expr();
    out(")");
}

void dovar() {
    auto s = cifylabel(gettok());
    out("var_{}", s);
}

void doglobalassign() {
    gettok();
    auto name = gettok();
    out("{} = ", globals.at(name));
    expr();
    out(";");
}

void doglobal() {
    auto name = gettok();
    out(globals.at(name));
}

void doblock() {
    gettok();
    out("({");
    while (toptok() != ")") {
        expr();
        out(";");
    }
    out("})");
}

void docfunc() {
    gettok();
    auto name = gettok();
    out("({");
    out(name);
    out("(");
    while (toptok() != ")") {
        if (name == "free" || name == "afree") {
            out("(void*)");
        }
        if (name == "writefile" || name == "readfile") {
            out("(char*)");
        }
        if (name == "printf" && toptok()[0] == '"') out(gettok());
        else expr();
        if (toptok() != ")") out(",");
    }
    out(");");
    if (name == "free" || name == "exit") {
        out("0;");
    }
    out("})");
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
    pushout();
    expr();
    auto arr = popout();
    pushout();
    expr();
    auto ind = popout();
    auto size = getint();
    pushout();
    expr();
    auto assign = popout();
    out("((({}*){})[{}] = {})", sizemap.at(size), arr, ind, assign);
}
 
void doarrayindex() {
    gettok();
    pushout();
    expr();
    auto arr = popout();
    pushout();
    expr();
    auto ind = popout();
    auto size = getint();
    out("((({}*){})[{}])", sizemap.at(size), arr, ind);
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
    if (mapcontainskey(ops, t)) doop(); //+use wrappers, -O3 will inline them
    else if (mapcontainskey(cmpops, t)) docmpop();
    else if (mapcontainskey(divops, t)) dodivop();
    else if (mapcontainskey(fltops, t)) dofltop();
    else if (toptok() == "<>") dofunc(); //+normal c func (need map to hold each func)
    else if (toptok() == "<>>") dopublicfunc();
    else if (toptok() == "?") doif(); //+ternary with statement expr
    else if (toptok() == "??") dowhile(); //+c while with expression statement returning 0
    else if (toptok() == "=") doassign(); //+use long type for first occurance
    else if (toptok() == ":=") doglobalassign(); //+see above
    else if (toptok() == "!!") doarrayindex(); //+a cast and an index
    else if (toptok() == "!:") doarrayassign(); //+see above
    else if (toptok() == "{}") doblock(); //+statement expr
    else if (toptok() == "@") docfunc(); //+lol
    //else if (toptok() == "><") doret();
    else if (toptok() == ">-") dobreak(); //+lol
    else if (toptok() == "\\>") doexeclambda(); //+lol
    else if (mapcontainskey(funcs, t)) docall(); //+lol
    else err("malformed s expression '{}'", t);
    match(")");
}

void expr(){
    auto t = toptok();
    if (t == "(") sexpr();
    else if (isint(t)) doint();
    else if (isFloat(t)) doflt();
    else if (veccontains(curvars, t)) dovar();
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
            std::vector<std::string> args;
            while (toptok() != ")") {
                args.push_back(gettok());
            }
            funclabels[name] = newname(name);
            if (s == "<>>") funclabels[name] = name;
            funcs[name] = args;
        } else if (s == ":=") {
            auto name = gettok();
            globals[name] = newname(name);
            dataout("gt {} = 0;", globals[name]);
        }
    }
    tokens = oldtokens;
}

void start(std::string src){
    tokens = tokenize(src);
    dataout("#include \"stdlib.h\"");
    dataout("#include \"stdint.h\"");
    dataout("#include \"stdio.h\"");
    dataout("#include \"math.h\"");
    dataout("#include \"time.h\"");
    dataout("#include \"file.c\"");
    dataout("#define opf(name, op) gt name(gt a, gt b){return a op b;}");
    dataout("#define fltopf(name, op) gt name(gt a, gt b){double c = *(double*)&a; double d = *(double*)&b; double result = c op d; return *(gt*)&result;}");
    dataout("typedef intptr_t gt;");
    for (auto k : getkeys(ops)) dataout("opf({}, {})", ops.at(k), k);
    for (auto k : getkeys(cmpops)) dataout("opf({}, {})", cmpops.at(k), k);
    for (auto k : getkeys(divops)) dataout("opf({}, {})", divops.at(k), k);
    for (auto k : getkeys(fltops)) dataout("fltopf({}, {})", fltops.at(k), k.substr(1));
    dataout("#undef opf");
    dataout("#undef fltopf");
    findfuncs();
    std::string mainname = "main";
    if (ismakeobject) mainname = cifylabel(newname("main"));
    out("int {}(int argc, char **argv){", mainname);
    auto name = "@argc";                                                                              
    globals[name] = newname(name);                                                                      
    dataout("gt {};", globals[name]);
    out("{} = (gt)argc;", globals[name]);
    name = "@argv";               
    globals[name] = newname(name);     
    dataout("gt {};", globals[name]); 
    out("{} = (gt)argv;", globals[name]);
    while (tokens.size() > 1) {
        expr();
        out(";");
    }
    out("}");
    //cout << output << endl;
    //auto asmmacros = readfile("asmmacros.txt");
    for (auto f : getkeys(funcbodies)) {
        out(funcbodies.at(f));
    }
    auto result = dataoutput + "\n" + output;
    writefile("rout.c", result);
    //system("clang -O3 rout.c 2>&1 | ./onlyshowerr");
}

int main(int argc, char ** argv) {
    /*
    if (argc < 2) {
        err("bad number of arguments");
    }
    */

    for (int i = 0; i < argc; i++) {
        std::string s = argv[i];
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
    
    fltops["f+"] = "fltadd";
    fltops["f-"] = "fltsub";
    fltops["f*"] = "fltmul";
    fltops["f/"] = "fltdiv";
    
    sizemap["1"] = "int8_t";
    sizemap["2"] = "int16_t";
    sizemap["4"] = "int32_t";
    sizemap["8"] = "int64_t";
    
    std::string src = "";
    for (std::string line; std::getline(std::cin, line);) {
        src += line + "\n";
    }
    src += "(@ exit 0)";
    start(src);
    
    return 0;
}

