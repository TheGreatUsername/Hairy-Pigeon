#pragma once 

#include <string>
#include <concepts>
#include <ranges>
#include <cstdlib>

namespace {
    constexpr std::string_view BRACES = "{}";

    template<typename T, typename... Ts>
    void fmt(std::ostream& os, std::string_view pattern, T&& t, Ts&&... ts) {
        if (auto found = pattern.find(BRACES); found != std::string::npos) {
            os << pattern.substr(0, found);
            os << t;

            if constexpr (sizeof...(ts) > 0) {
                fmt(os, pattern.substr(found + BRACES.size()), std::forward<Ts>(ts)...);
            } else {
                os << pattern.substr(found + BRACES.size());
            }
        } else {
            throw std::runtime_error{"Number of format args does not match number of placeholders"};
        }
    }
}

template<typename... Args>
std::string format(std::string_view pattern, Args&&... args) {
    if constexpr (sizeof...(args) == 0) {
        return { pattern.data(), pattern.size() };
    } else {
        std::stringstream ss;
        fmt(ss, pattern, std::forward<Args>(args)...);
        return ss.str();
    }
}
