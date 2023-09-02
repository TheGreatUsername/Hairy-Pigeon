project(HairyPigoenCompiler
    VERSION 0.1
    LANGUAGES CXX)

FORMAT_TARGET = "format"
SEIR_TARGET = "SEIR"
SEIRC_TARGET = "SEIRC"

#format
add_library(${FORMAT_TARGET} SHARED
    format.cpp 
)

target_compile_options(${FORMAT_TARGET} -std=++20 -03)

#seir
add_executable(${SEIR_TARGET} 
    SEIR.cpp 
)

target_compile_options(${SEIR_TARGET} -std=c++20 -O3)

target_link_libraries(${SEIR_TARGET} 
PRIVATE
    ${FORMAT_TARGET}
)

#seirc
add_executable(${SEIRC_TARGET}
    SEIRC.cpp 
)

target_compile_options(${SEIRC_TARGET} -std=c++20 -O3)

target_link_libraries(${SEIRC_TARGET} 
PRIVATE
    ${FORMAT_TARGET}
)