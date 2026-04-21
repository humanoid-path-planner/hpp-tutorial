#
# Copyright (c) 2014, 2020 CNRS Authors: Florent Lamiraux,  Guilhem Saurel
#
# This file is part of hpp_tutorial hpp_tutorial is free software: you can
# redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3
# of the License, or (at your option) any later version.
#
# hpp_tutorial is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Lesser Public License for more
# details.  You should have received a copy of the GNU Lesser General Public
# License along with hpp_tutorial  If not, see <http://www.gnu.org/licenses/>.

cmake_minimum_required(VERSION 3.22)

set(PROJECT_NAME hpp_tutorial)
set(PROJECT_DESCRIPTION "Tutorial for humanoid path planner platform.")

set(PROJECT_USE_CMAKE_EXPORT TRUE)
set(CXX_DISABLE_WERROR TRUE)

# Check if the submodule cmake have been initialized
set(JRL_CMAKE_MODULES "${CMAKE_CURRENT_LIST_DIR}/cmake")
if(EXISTS "${JRL_CMAKE_MODULES}/base.cmake")
    message(STATUS "JRL cmakemodules found in 'cmake/' git submodule")
else()
    find_package(jrl-cmakemodules QUIET CONFIG)
    if(jrl-cmakemodules_FOUND)
        get_property(
            JRL_CMAKE_MODULES
            TARGET jrl-cmakemodules::jrl-cmakemodules
            PROPERTY INTERFACE_INCLUDE_DIRECTORIES
        )
        message(
            STATUS
            "JRL cmakemodules found on system at ${JRL_CMAKE_MODULES}"
        )
    else()
        message(STATUS "JRL cmakemodules not found. Let's fetch it.")
        include(FetchContent)
        FetchContent_Declare(
            "jrl-cmakemodules"
            GIT_REPOSITORY "https://github.com/jrl-umi3218/jrl-cmakemodules.git"
        )
        FetchContent_MakeAvailable("jrl-cmakemodules")
        FetchContent_GetProperties(
            "jrl-cmakemodules"
            SOURCE_DIR JRL_CMAKE_MODULES
        )
    endif()
endif()

include("${JRL_CMAKE_MODULES}/hpp.cmake")
include("${JRL_CMAKE_MODULES}/python.cmake")

compute_project_args(PROJECT_ARGS LANGUAGES CXX)
project(${PROJECT_NAME} ${PROJECT_ARGS})

add_project_dependency("hpp-manipulation" REQUIRED)
add_project_dependency("example-robot-data" REQUIRED)
add_project_dependency("hpp-gepetto-viewer" REQUIRED)

if(NOT FINDPYTHON_ALREADY_CALLED)
    findpython()
endif()

set(CATKIN_PACKAGE_SHARE_DESTINATION
    ${CMAKE_INSTALL_DATAROOTDIR}/${PROJECT_NAME}
)

install(DIRECTORY urdf DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})
install(DIRECTORY srdf DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})
install(DIRECTORY meshes DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})
install(DIRECTORY tutorial_6 DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})
install(DIRECTORY launch DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})

install(
    FILES Media/models/meshes/glasses/__Color_A05_4.png
    DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/Media/models/meshes/glasses
)

install(
    FILES
        Media/materials/textures/ganz_rechts_neben_kuecheninsel.png
        Media/materials/textures/hinter_shopschraenken_an_saeule.png
        Media/materials/textures/wallpaper_ai_unihb.png
        Media/materials/textures/stove.png
        Media/materials/textures/ganz_links_vorn_bei_biolab.png
        Media/materials/textures/wallpaper2.png
        Media/materials/textures/ganz_links_neben_roboterplakat.png
        Media/materials/textures/auf_saeule_bei_shop.png
        Media/materials/textures/wallpaper_project_logos.png
        Media/materials/textures/wallpaper.png
        Media/materials/textures/sink.png
        Media/materials/textures/mittig_neben_roboterplakat.png
    DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/Media/materials/textures
)

add_library(${PROJECT_NAME} INTERFACE)
install(TARGETS ${PROJECT_NAME} EXPORT ${TARGETS_EXPORT_NAME} DESTINATION lib)
