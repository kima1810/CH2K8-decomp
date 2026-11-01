# ch2k8 - ReXGlue Recompiled Project
#
# SDK boilerplate lives in generated/rexglue.cmake (written by `rexglue codegen`).

cmake_minimum_required(VERSION 3.25)
project(ch2k8 VERSION 0.0.1 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Python3 3.11 REQUIRED COMPONENTS Interpreter)

# Keep the generated SDK boilerplate intact. Include a build-directory copy
# whose codegen command preserves the manifest timestamp after a no-op rewrite.
# Otherwise the pinned SDK's final sdk_version rewrite makes Ninja dirty again.
set(CH2K8_SDK_CMAKE "${CMAKE_CURRENT_SOURCE_DIR}/generated/rexglue.cmake")
file(READ "${CH2K8_SDK_CMAKE}" CH2K8_SDK_CMAKE_CONTENT)
set(CH2K8_ORIGINAL_CODEGEN
    "COMMAND $<TARGET_FILE:rex::rexglue> codegen \${CMAKE_CURRENT_SOURCE_DIR}/ch2k8_manifest.toml")
string(FIND "${CH2K8_SDK_CMAKE_CONTENT}" "${CH2K8_ORIGINAL_CODEGEN}" CH2K8_COMMAND_OFFSET)
if(CH2K8_COMMAND_OFFSET EQUAL -1)
    message(FATAL_ERROR "Unrecognized SDK codegen command; use the documented pinned SDK")
endif()
string(REPLACE "${CH2K8_ORIGINAL_CODEGEN}"
    "COMMAND \"${Python3_EXECUTABLE}\" \"${CMAKE_CURRENT_SOURCE_DIR}/../tools/run_codegen.py\" $<TARGET_FILE:rex::rexglue> \"${CMAKE_CURRENT_SOURCE_DIR}/ch2k8_manifest.toml\" \"${CMAKE_CURRENT_SOURCE_DIR}/generated/default\""
    CH2K8_SDK_CMAKE_CONTENT "${CH2K8_SDK_CMAKE_CONTENT}")
file(CONFIGURE OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/rexglue.cmake"
    CONTENT "${CH2K8_SDK_CMAKE_CONTENT}" @ONLY)
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${CH2K8_SDK_CMAKE}")
include("${CMAKE_CURRENT_BINARY_DIR}/rexglue.cmake")

option(CH2K8_REQUIRE_VULKAN "Require a Vulkan-capable installed SDK" OFF)
if(CH2K8_REQUIRE_VULKAN)
    get_target_property(CH2K8_SDK_DEFINITIONS rex::runtime INTERFACE_COMPILE_DEFINITIONS)
    if(NOT "REX_HAS_VULKAN=1" IN_LIST CH2K8_SDK_DEFINITIONS)
        message(FATAL_ERROR "Vulkan SDK required. Run tools/build_vulkan_sdk.ps1 first; the default Windows SDK is D3D12-only.")
    endif()
endif()

set(CH2K8_SOURCES
    src/main.cpp
    src/frame_timing.cpp
    src/output_capture.cpp
    src/hot_functions.cpp
)

if(WIN32)
    add_executable(ch2k8 WIN32 ${CH2K8_SOURCES})
else()
    add_executable(ch2k8 ${CH2K8_SOURCES})
endif()

rexglue_setup_target(ch2k8 GPU_PLUGINS xenos)
if(WIN32)
    # The GPU plugin is loaded dynamically, so an SDK DLL change need not change
    # an import library. Relink to run the SDK's POST_BUILD DLL staging commands.
    set_property(TARGET ch2k8 APPEND PROPERTY LINK_DEPENDS
        "$<TARGET_FILE:rex::gpu-xenos>" "$<TARGET_FILE:rex::runtime>")
endif()
# Public Vulkan provider headers reference the RenderDoc application API; the
# pinned SDK does not install that dependency's header. Use our licensed copy.
target_include_directories(ch2k8 PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/third_party")
target_compile_definitions(ch2k8 PRIVATE CH2K8_VERSION="${PROJECT_VERSION}")
if(WIN32)
    # Preserve the generated code's line tables in a PDB for startup debugging.
    target_link_options(ch2k8 PRIVATE "LINKER:/DEBUG:FULL" "LINKER:/INCREMENTAL:NO")
endif()

# SDK 0.10.0.24 emits a 32-bit cast before a 44-bit arithmetic shift for
# vupkd3d128's packed signed 20-bit lanes. Correct only those exact expressions
# after codegen and before compilation; never hand-edit generated sources.
if(TARGET ch2k8_recomp)
    # The pinned SDK rewrites sdk_version in the manifest after writing its
    # build stamp, even if the text is unchanged. Stamp completion last so the
    # manifest does not make codegen (and every object) dirty on every build.
    add_custom_command(
        OUTPUT "${CMAKE_CURRENT_SOURCE_DIR}/generated/default/codegen.build.stamp"
        APPEND
        DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/../tools/run_codegen.py"
                "${CMAKE_CURRENT_SOURCE_DIR}/../tools/fix_codegen.py"
                "${CMAKE_CURRENT_SOURCE_DIR}/../tools/optimize_codegen.py"
                "${CMAKE_CURRENT_SOURCE_DIR}/../tools/prove_vector_store_ranges.py"
        COMMAND "${CMAKE_COMMAND}" -E touch
                "${CMAKE_CURRENT_SOURCE_DIR}/generated/default/codegen.build.stamp"
    )
    target_compile_options(ch2k8_recomp PRIVATE
        $<$<CXX_COMPILER_ID:Clang,AppleClang>:-Werror=shift-count-overflow>)
endif()
