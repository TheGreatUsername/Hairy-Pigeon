cmake_minimum_required(VERSION 3.2)

project(HairyPigoenCompiler
    VERSION 0.1
    LANGUAGES CXX)

set(SEIR_TARGET "SEIR")
set(SEIRC_TARGET "SEIRC")
set(LIBSEIR_TARGET "libSEIR")

#seirlib
add_library(${LIBSEIR_TARGET} SHARED

)

#seir
add_executable(${SEIR_TARGET} 
    SEIR.cpp 
)

target_compile_options(${SEIR_TARGET} PRIVATE -std=c++20 -O3)

#seirc
add_executable(${SEIRC_TARGET}
    SEIRC.cpp 
)

target_compile_options(${SEIRC_TARGET} PRIVATE -std=c++20 -O3)