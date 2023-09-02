#pragma once 

#include <string>
#include <concepts>
#include <string_view>

namespace {
    
}

template<typename... Args>
std::string format(std::string pattern, Args&&... args) {
    if constexpr (sizeof...(args) == 0) {
        return  pattern;
    } else {
                
    }
}

// template<typename T, typename... Args>
// std::string format(std::string_view s, T value, Args... args) {
//     if (s.find("{}") != std::std::string::npos) {
//         auto foundat = s.find("{}");
//         return s.substr(0, foundat + 2) % value + format(s.substr(foundat + 2, s.size() - (foundat + 2)), args...);
//     }
//     return s;
// }

