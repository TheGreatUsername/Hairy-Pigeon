#include "format.hpp"

std::string operator % (std::string_view src, std::string insert) {
    if (src.length() <= 1) { throw std::runtime_error("No {} found"); }
    char c = src[0];
    //std::string s = src.substr(1);
    return c == '{' && src[1] == '}' ? insert + src.substr(2) : c + src % insert;
}

std::string operator % (std::string_view src, int n) {
    return src % std::to_string(n);
}

std::string format(std::string_view s) {
    return s;
}


