cmake_minimum_required(VERSION 3.10)
project(KeyLogger C)

set(CMAKE_C_STANDARD 11)

# Include current directory to find sqlite3.h
include_directories(${CMAKE_SOURCE_DIR})

# Add main.c and sqlite3.c to the build
add_executable(${PROJECT_NAME} main.c sqlite3.c)

# Platform-specific linking
if(UNIX AND NOT APPLE)
    target_link_libraries(${PROJECT_NAME} dl pthread)
endif()

if(WIN32)
    target_link_libraries(${PROJECT_NAME} user32 psapi)
endif()