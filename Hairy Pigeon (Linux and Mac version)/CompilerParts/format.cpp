#include <iostream>
#include <string>

using namespace std;

string operator % (string src, string insert) {
    if (src.length() <= 1) throw runtime_error("No {} found");
    char c = src[0];
    string s = src.substr(1);
    return c == '{' && s[0] == '}' ? insert + s.substr(1) : c + s % insert;
}

string operator % (string src, int n) {
    return src % to_string(n);
}

string format(string s) {
    return s;
}

template<typename T, typename... Args>
string format(string s, T value, Args... args) {
    if (s.find("{}") != std::string::npos) {
        auto foundat = s.find("{}");
        return s.substr(0, foundat + 2) % value + format(s.substr(foundat + 2, s.size() - (foundat + 2)), args...);
    }
    return s;
}
