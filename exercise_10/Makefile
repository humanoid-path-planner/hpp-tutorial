#
# Copyright (c) 2014 CNRS-LAAS
# Author: Florent Lamiraux
#

HPP_REPO=git@github.com:humanoid-path-planner
JRL_REPO=https://github.com/jrl-umi3218
TOPPRA_REPO=https://github.com/hungpham2511
GITLAB_FLORENT=git@gitlab.laas.fr:florent
MFJA_REPO=https://github.com/aip-primeca-occitanie

SRC_DIR=${DEVEL_HPP_DIR}/src
ifndef INSTALL_HPP_DIR
INSTALL_HPP_DIR=${DEVEL_HPP_DIR}/install
endif

BUILD_TYPE=Release
BUILD_TESTING=OFF
ifeq (${BUILD_TYPE},Debug)
  BUILD_FOLDER=build
else
  BUILD_FOLDER=build-rel
  BUILD_TESTING=OFF
endif

WGET=wget --quiet
UNZIP=unzip -qq
TAR=tar
GIT_QUIET=--quiet
# Qt version should be either 4 or 5
QT_VERSION=5
INSTALL_DOCUMENTATION=ON
BUILD_JOBS=4

##################################
# {{{ Dependencies

# }}}
##################################
# {{{ Packages supporting HPP_VERSION

# Either a version tag (e.g. v4.3.0), stable or devel
HPP_VERSION=devel
HPP_EXTRA_FLAGS= -DBUILD_TESTING=${BUILD_TESTING} -DAUTO_UNINSTALL=OFF -DDOXYGEN_GENERATE_XML=YES

hpp-constraints_branch=${HPP_VERSION}
hpp-constraints_repository=${HPP_REPO}
hpp-constraints_extra_flags=${HPP_EXTRA_FLAGS}

hpp-core_branch=${HPP_VERSION}
hpp-core_repository=${HPP_REPO}
hpp-core_extra_flags=${HPP_EXTRA_FLAGS}

hpp-python_branch=${HPP_VERSION}
hpp-python_repository=${HPP_REPO}
hpp-python_extra_flags=${HPP_EXTRA_FLAGS} -DPYTHON_STANDARD_LAYOUT=ON

hpp-doc_branch=${HPP_VERSION}
hpp-doc_repository=${HPP_REPO}

hpp-manipulation_branch=${HPP_VERSION}
hpp-manipulation_repository=${HPP_REPO}
hpp-manipulation_extra_flags= ${HPP_EXTRA_FLAGS}

hpp-manipulation-urdf_branch=${HPP_VERSION}
hpp-manipulation-urdf_repository=${HPP_REPO}
hpp-manipulation-urdf_extra_flags=${HPP_EXTRA_FLAGS}

hpp_tutorial_branch=${HPP_VERSION}
hpp_tutorial_repository=${HPP_REPO}
hpp_tutorial_extra_flags=${HPP_EXTRA_FLAGS} -DPYTHON_STANDARD_LAYOUT=ON

hpp-practicals_branch=${HPP_VERSION}
hpp-practicals_repository=${HPP_REPO}
hpp-practicals_extra_flags=${HPP_EXTRA_FLAGS} -DPYTHON_STANDARD_LAYOUT=ON

hpp-gepetto-viewer_branch=${HPP_VERSION}
hpp-gepetto-viewer_repository=${HPP_REPO}
hpp-gepetto-viewer_extra_flags= -DINSTALL_DOCUMENTATION=OFF -DUSE_HPP_PYTHON=ON \
	-DPYTHON_STANDARD_LAYOUT=ON

hpp-plot_branch=${HPP_VERSION}
hpp-plot_repository=${HPP_REPO}
hpp-plot_extra_flags= -DINSTALL_DOCUMENTATION=OFF

hpp-exec_branch=${HPP_VERSION}
hpp-exec_repository=${HPP_REPO}
hpp-exec_extra_flags=${PYTHON_FLAGS}

nimblebot-description_repository=${GITLAB_FLORENT}
nimblebot-description_branch=main
nimblebot-description_extra_flags=

# }}}
##################################
# {{{ Packages for toppra

toppra_repository=${TOPPRA_REPO}
toppra_branch=0.6.7
toppra_extra_flags= -DBUILD_TESTS=OFF -DPYTHON_BINDINGS=OFF

hpp-toppra_branch=${HPP_VERSION}
hpp-toppra_repository=${HPP_REPO}
hpp-toppra_extra_flags= -DPYTHON_STANDARD_LAYOUT=ON

# }}}
##################################
# {{{ Packages for MFJA

mfja_3rd_floor_gz_repository=${MFJA_REPO}
mfja_3rd_floor_gz_branch=devel

# }}}
##################################
# {{{ High-level targets

all: hpp-plot.install hpp_tutorial.install hpp-toppra.install
	${MAKE} hpp-doc.install

# }}}
##################################
# {{{ python virtual environment
python-venv:
	if [ -f ${INSTALL_HPP_DIR}/pyvenv.cfg ]; then \
		echo "python virtual environment already created in $INSTALL_HPP_DIR"; \
	else \
		python -m venv --system-site-packages ${INSTALL_HPP_DIR}; \
		${INSTALL_HPP_DIR}/bin/pip install --prefix=${INSTALL_HPP_DIR} \
			"numpy==1.26.4" trimesh pycollada viser; \
	fi

# }}}
##################################
# {{{ Dependencies declaration

hpp-doc.configure.dep: hpp-doc.checkout
hpp-constraints.configure.dep: hpp-constraints.checkout
hpp-core.configure.dep: hpp-core.checkout hpp-constraints.install
hpp-manipulation.configure.dep: hpp-manipulation.checkout hpp-core.install
hpp-manipulation-urdf.configure.dep: hpp-manipulation-urdf.checkout hpp-manipulation.install
hpp-python.configure.dep: hpp-python.checkout hpp-manipulation-urdf.install
hpp-plot.configure.dep: hpp-plot.checkout hpp-manipulation.install
hpp_tutorial.configure.dep: hpp_tutorial.checkout hpp-gepetto-viewer.install \
	hpp-python.install mfja_3rd_floor_description.install mfja_robot_control_config.install \
	mfja_staubli_manipulation_demos.install
hpp-gepetto-viewer.configure.dep: hpp-gepetto-viewer.checkout python-venv hpp-python.install
toppra.configure.dep: toppra.checkout
hpp-toppra.configure.dep: hpp-toppra.checkout toppra.install
hpp-exec.configure.dep: hpp-exec.checkout
hpp-practicals.configure.dep: hpp-practicals.checkout hpp-manipulation-urdf.install \
	hpp-gepetto-viewer.install
nimblebot-description.configure.dep: nimblebot-description.checkout
mfja_3rd_floor_description.configure.dep: mfja_3rd_floor_gz.checkout
mfja_robot_control_config.configure.dep: mfja_3rd_floor_gz.checkout
mfja_staubli_manipulation_demos.configure.dep: mfja_3rd_floor_gz.checkout

# }}}
##################################
# {{{ Targets

status:
	@for child_dir in $$(ls ${SRC_DIR}); do \
		test -d "$$child_dir" || continue; \
		test -d "$$child_dir/.git" || continue; \
		${MAKE} "$$child_dir".status; \
	done

log:
	@for child_dir in $$(ls ${SRC_DIR}); do \
		test -d "$$child_dir" || continue; \
		test -d "$$child_dir/.git" || continue; \
		${MAKE} "$$child_dir".log; \
	done

fetch:
	@for child_dir in $$(ls ${SRC_DIR}); do \
		test -d "$$child_dir" || continue; \
		test -d "$$child_dir/.git" || continue; \
		${MAKE} "$$child_dir".fetch; \
	done

update:
	@for child_dir in $$(ls ${SRC_DIR}); do \
		test -d "$$child_dir" || continue; \
		test -d "$$child_dir/.git" || continue; \
		${MAKE} "$$child_dir".update; \
	done

test:
	@for child_dir in $$(ls ${SRC_DIR}); do \
		test -d "$$child_dir" || continue; \
		test -d "$$child_dir/.git" || continue; \
		${MAKE} "$$child_dir".test; \
	done

%.checkout:
	if [ -d $(@:.checkout=)/.git ]; then \
		echo "$(@:.checkout=) already checkout out."; \
	else \
		git clone ${GIT_QUIET} -b ${$(@:.checkout=)_branch} ${$(@:.checkout=)_repository}/$(@:.checkout=); \
	fi \

%.fetch:
	if [ "${$(@:.fetch=)_repository}" = "" ]; then \
		echo "$(@:.fetch=) is not referenced"; \
	else \
		cd ${SRC_DIR}/$(@:.fetch=);\
		git fetch ${GIT_QUIET} origin; \
		git fetch ${GIT_QUIET} origin --tags; \
	fi

%.update:
	if [ "${$(@:.update=)_repository}" = "" ]; then \
		echo "$(@:.update=) is not referenced"; \
	else \
		cd ${SRC_DIR}/$(@:.update=);\
		git remote rm origin;\
		git remote add origin ${$(@:.update=)_repository}/$(@:.update=);\
		git fetch origin;\
		git fetch origin --tags;\
		git checkout -q --detach;\
		git branch -f ${$(@:.update=)_branch} origin/${$(@:.update=)_branch};\
		git checkout -q ${$(@:.update=)_branch}; \
	fi


%.configure: %.configure.dep
	${MAKE} $(@:.configure=).configure_nodep

%.configure-py: %.configure-py.dep
	${MAKE} $(@:.configure-py=).configure_nodep-py

%.configure_nodep:%.checkout
	cmake \
		-DAUTO_UNINSTALL=OFF \
		-DBUILD_PYTHON_INTERFACE=OFF \
		-DCMAKE_INSTALL_PREFIX=${INSTALL_HPP_DIR} \
		-DCMAKE_INSTALL_LIBDIR=lib \
		-DCMAKE_BUILD_TYPE=${BUILD_TYPE} \
		-DENFORCE_MINIMAL_CXX_STANDARD=ON \
		-DINSTALL_DOCUMENTATION=${INSTALL_DOCUMENTATION} \
		-DCMAKE_CXX_FLAGS_RELWITHDEBINFO="-g -O3 -DNDEBUG" \
		${$(@:.configure_nodep=)_extra_flags} \
		-B ${SRC_DIR}/$(@:.configure_nodep=)/${BUILD_FOLDER} \
		-S ${SRC_DIR}/$(@:.configure_nodep=)

%.configure_nodep-py:%.checkout
	cmake \
		-DAUTO_UNINSTALL=OFF \
		-DBUILD_PYTHON_INTERFACE=ON \
		-DBUILD_STANDALONE_PYTHON_INTERFACE=ON \
		-DCMAKE_INSTALL_PREFIX=${INSTALL_HPP_DIR} \
		-DCMAKE_INSTALL_LIBDIR=lib \
		-DCMAKE_BUILD_TYPE=${BUILD_TYPE} \
		-DENFORCE_MINIMAL_CXX_STANDARD=ON \
		-DINSTALL_DOCUMENTATION=${INSTALL_DOCUMENTATION} \
		-DCMAKE_CXX_FLAGS_RELWITHDEBINFO="-g -O3 -DNDEBUG" \
		${$(@:.configure_nodep-py=)_extra_flags} \
		-B ${SRC_DIR}/$(@:.configure_nodep-py=)/${BUILD_FOLDER}-py \
		-S ${SRC_DIR}/$(@:.configure_nodep-py=)


%.build:%.configure
	cmake --build ${SRC_DIR}/$(@:.build=)/${BUILD_FOLDER} -j $(or $($(@:.build=)_jobs),${BUILD_JOBS})

%.build-py:%.configure-py
	cmake --build ${SRC_DIR}/$(@:.build-py=)/${BUILD_FOLDER}-py -j $(or $($(@:.build-py=)_jobs),${BUILD_JOBS})

%.test:%.build
	cmake --build ${SRC_DIR}/$(@:.test=)/${BUILD_FOLDER} -t test

%.test-py:%.build-py
	cmake --build ${SRC_DIR}/$(@:.test-py=)/${BUILD_FOLDER}-py -t test

%.install:%.build
	cmake --build ${SRC_DIR}/$(@:.install=)/${BUILD_FOLDER} -t install

%.install-py:%.build-py
	cmake --build ${SRC_DIR}/$(@:.install-py=)/${BUILD_FOLDER}-py -t install

%.install_nodep:%.configure_nodep
	cmake --build ${SRC_DIR}/$(@:.install_nodep=)/${BUILD_FOLDER} -t install

%.install_nodep-py:%.configure_nodep-py
	cmake --build ${SRC_DIR}/$(@:.install_nodep-py=)/${BUILD_FOLDER}-py -t install

%.uninstall:
	cmake --build ${SRC_DIR}/$(@:.uninstall=)/${BUILD_FOLDER} -t uninstall

%.uninstall-py:
	cmake --build ${SRC_DIR}/$(@:.uninstall-py=)/${BUILD_FOLDER}-py -t uninstall

%.clean:
	cmake --build ${SRC_DIR}/$(@:.clean=)/${BUILD_FOLDER} -t clean

%.clean-py:
	cmake --build ${SRC_DIR}/$(@:.clean-py=)/${BUILD_FOLDER}-py -t clean

%.very-clean:
	rm -rf ${SRC_DIR}/$(@:.very-clean=)/${BUILD_FOLDER}/*

%.very-clean-py:
	rm -rf ${SRC_DIR}/$(@:.very-clean-py=)/${BUILD_FOLDER}-py/*

%.status:
	@cd ${SRC_DIR}/$(@:.status=); \
	echo \
	"\033[1;36m------- Folder $(@:.status=) ---------------\033[0m"; \
	git --no-pager -c status.showUntrackedFiles=no status --short --branch;\

%.log:
	@cd ${SRC_DIR}/$(@:.log=); \
	if [ -f .git/refs/heads/${$(@:.log=)_branch} ]; then \
		echo -n "$(@:.log=): "; \
		cat .git/refs/heads/${$(@:.log=)_branch}; \
	fi

toppra.configure_nodep:toppra.checkout
	mkdir -p ${SRC_DIR}/$(@:.configure_nodep=)/cpp/${BUILD_FOLDER}; \
	cd ${SRC_DIR}/$(@:.configure_nodep=)/cpp/${BUILD_FOLDER}; \
	cmake -DCMAKE_INSTALL_PREFIX=${INSTALL_HPP_DIR} -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_BUILD_TYPE=${BUILD_TYPE} \
			-DENFORCE_MINIMAL_CXX_STANDARD=ON \
			-DINSTALL_DOCUMENTATION=${INSTALL_DOCUMENTATION} \
			-DCMAKE_CXX_FLAGS_RELWITHDEBINFO="-g -O3 -DNDEBUG" \
			${CLANG_FLAGS} \
			${$(@:.configure_nodep=)_extra_flags} ..

toppra.install:toppra.configure
	${MAKE} -C ${SRC_DIR}/$(@:.install=)/cpp/${BUILD_FOLDER} install

toppra.install_nodep:toppra.configure_nodep
	${MAKE} -C ${SRC_DIR}/$(@:.install_nodep=)/cpp/${BUILD_FOLDER} install

mfja_3rd_floor_description.configure_nodep: mfja_3rd_floor_gz.checkout
	mkdir -p ${SRC_DIR}/mfja_3rd_floor_gz/$(@:.configure_nodep=)/${BUILD_FOLDER}; \
	cd ${SRC_DIR}/mfja_3rd_floor_gz/$(@:.configure_nodep=)/${BUILD_FOLDER}; \
	cmake -DCMAKE_INSTALL_PREFIX=${INSTALL_HPP_DIR} -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_BUILD_TYPE=${BUILD_TYPE} \
			-DENFORCE_MINIMAL_CXX_STANDARD=ON \
			-DINSTALL_DOCUMENTATION=${INSTALL_DOCUMENTATION} \
			-DCMAKE_CXX_FLAGS_RELWITHDEBINFO="-g -O3 -DNDEBUG" \
			${CLANG_FLAGS} \
			${$(@:.configure_nodep=)_extra_flags} ..

mfja_3rd_floor_description.install:mfja_3rd_floor_description.configure
	${MAKE} -C ${SRC_DIR}/mfja_3rd_floor_gz/$(@:.install=)/${BUILD_FOLDER} install

mfja_3rd_floor_description.install_nodep:mfja_3rd_floor_description.configure_nodep
	${MAKE} -C ${SRC_DIR}/mfja_3rd_floor_gz/$(@:.install_nodep=)/${BUILD_FOLDER} install

mfja_robot_control_config.configure_nodep: mfja_3rd_floor_gz.checkout
	mkdir -p ${SRC_DIR}/mfja_3rd_floor_gz/$(@:.configure_nodep=)/${BUILD_FOLDER}; \
	cd ${SRC_DIR}/mfja_3rd_floor_gz/$(@:.configure_nodep=)/${BUILD_FOLDER}; \
	cmake -DCMAKE_INSTALL_PREFIX=${INSTALL_HPP_DIR} -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_BUILD_TYPE=${BUILD_TYPE} \
			-DENFORCE_MINIMAL_CXX_STANDARD=ON \
			-DINSTALL_DOCUMENTATION=${INSTALL_DOCUMENTATION} \
			-DCMAKE_CXX_FLAGS_RELWITHDEBINFO="-g -O3 -DNDEBUG" \
			${CLANG_FLAGS} \
			${$(@:.configure_nodep=)_extra_flags} ..

mfja_robot_control_config.install:mfja_robot_control_config.configure
	${MAKE} -C ${SRC_DIR}/mfja_3rd_floor_gz/$(@:.install=)/${BUILD_FOLDER} install

mfja_robot_control_config.install_nodep:mfja_robot_control_config.configure_nodep
	${MAKE} -C ${SRC_DIR}/mfja_3rd_floor_gz/$(@:.install_nodep=)/${BUILD_FOLDER} install

mfja_staubli_manipulation_demos.configure_nodep: mfja_3rd_floor_gz.checkout
	mkdir -p ${SRC_DIR}/mfja_3rd_floor_gz/$(@:.configure_nodep=)/${BUILD_FOLDER}; \
	cd ${SRC_DIR}/mfja_3rd_floor_gz/$(@:.configure_nodep=)/${BUILD_FOLDER}; \
	cmake -DCMAKE_INSTALL_PREFIX=${INSTALL_HPP_DIR} -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_BUILD_TYPE=${BUILD_TYPE} \
			-DENFORCE_MINIMAL_CXX_STANDARD=ON \
			-DINSTALL_DOCUMENTATION=${INSTALL_DOCUMENTATION} \
			-DCMAKE_CXX_FLAGS_RELWITHDEBINFO="-g -O3 -DNDEBUG" \
			${CLANG_FLAGS} \
			${$(@:.configure_nodep=)_extra_flags} ..

mfja_staubli_manipulation_demos.install:mfja_staubli_manipulation_demos.configure
	${MAKE} -C ${SRC_DIR}/mfja_3rd_floor_gz/$(@:.install=)/${BUILD_FOLDER} install

mfja_staubli_manipulation_demos.install_nodep:mfja_staubli_manipulation_demos.configure_nodep
	${MAKE} -C ${SRC_DIR}/mfja_3rd_floor_gz/$(@:.install_nodep=)/${BUILD_FOLDER} install

# }}}

# vim: foldmethod=marker foldlevel=0
