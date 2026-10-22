# ch2k8 - ReXGlue Recompiled Project
#
# SDK boilerplate lives in generated/rexglue.cmake (written by `rexglue codegen`).

cmake_minimum_required(VERSION 3.25)
project(ch2k8 VERSION 0.0.1 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(generated/rexglue.cmake)

set(CH2K8_SOURCES
    src/main.cpp
)

if(WIN32)
    add_executable(ch2k8 WIN32 ${CH2K8_SOURCES})
else()
    add_executable(ch2k8 ${CH2K8_SOURCES})
endif()

rexglue_setup_target(ch2k8 GPU_PLUGINS xenos)
target_compile_definitions(ch2k8 PRIVATE CH2K8_VERSION="${PROJECT_VERSION}")
