cmake_minimum_required(VERSION 3.20)
project(RednessCam LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Windows SDK path (adjust if needed to match your SDK version)
# The MFCreateVirtualCamera API requires Windows 11 22H2 (SDK 10.0.22621.0 or later).
set(WIN_SDK_VER "10.0.26100.0")
set(WIN_SDK_ROOT "C:/Program Files (x86)/Windows Kits/10")
set(WIN_SDK_LIB "${WIN_SDK_ROOT}/Lib/${WIN_SDK_VER}/um/x64")
set(WIN_SDK_INC "${WIN_SDK_ROOT}/Include/${WIN_SDK_VER}/um")
set(WIN_SDK_SHARED "${WIN_SDK_ROOT}/Include/${WIN_SDK_VER}/shared")
set(WIN_SDK_WINRT "${WIN_SDK_ROOT}/Include/${WIN_SDK_VER}/winrt")
set(WIN_SDK_CPPWINRT "${WIN_SDK_ROOT}/Include/${WIN_SDK_VER}/cppwinrt")

# Shared compiler definitions
add_compile_definitions(
    _WIN32_WINNT=0x0A00
    NTDDI_VERSION=0x0A00000B
    UNICODE
    _UNICODE
    WIN32_LEAN_AND_MEAN
)

# Common include directories
set(COMMON_INCLUDES
    ${CMAKE_CURRENT_SOURCE_DIR}
    "${WIN_SDK_INC}"
    "${WIN_SDK_SHARED}"
    "${WIN_SDK_WINRT}"
    "${WIN_SDK_CPPWINRT}"
)

# 1. Build the Virtual Camera COM DLL (RednessCamSource.dll)
add_library(RednessCamSource SHARED
    DllMain.cpp
    MediaSource.cpp
    MediaStream.cpp
    FrameServer.cpp
    RednessCamSource.def
)
target_include_directories(RednessCamSource PRIVATE ${COMMON_INCLUDES})
target_link_directories(RednessCamSource PRIVATE "${WIN_SDK_LIB}")
target_link_libraries(RednessCamSource PRIVATE
    mf.lib
    mfplat.lib
    mfuuid.lib
    user32.lib
    ole32.lib
    advapi32.lib
)

# 2. Build the Host Executable (RednessCamHost.exe)
add_executable(RednessCamHost RednessCamHost.cpp)
target_include_directories(RednessCamHost PRIVATE ${COMMON_INCLUDES})
target_link_directories(RednessCamHost PRIVATE "${WIN_SDK_LIB}")
target_link_libraries(RednessCamHost PRIVATE
    mf.lib
    mfplat.lib
    mfuuid.lib
    mfsensorgroup.lib
    ole32.lib
)
