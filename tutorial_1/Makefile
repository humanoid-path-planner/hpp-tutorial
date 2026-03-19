#
# Copyright (c) 2014 CNRS-LAAS
# Author: Florent Lamiraux
#

HPP_REPO=https://github.com/humanoid-path-planner
FLORENT_REPO=https://github.com/florent-lamiraux
JRL_REPO=https://github.com/jrl-umi3218

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
PYTHON_FLAGS=-DPYTHON_STANDARD_LAYOUT=ON

##################################
# {{{ Dependencies

HPP_EXTRA_FLAGS= -DBUILD_TESTING=${BUILD_TESTING}

jrl-cmakemodules_branch=master
jrl-cmakemodules_repository=${JRL_REPO}

hpp-python_branch=devel
hpp-python_repository=${HPP_REPO}
hpp-python_extra_flags=${HPP_EXTRA_FLAGS} ${PYTHON_FLAGS}

hpp-doc_branch=devel
hpp-doc_repository=${HPP_REPO}

hpp_tutorial_branch=devel
hpp_tutorial_repository=${FLORENT_REPO}
hpp_tutorial_extra_flags=${HPP_EXTRA_FLAGS} ${PYTHON_FLAGS}

hpp-gepetto-viewer_branch=devel
hpp-gepetto-viewer_repository=${HPP_REPO}
hpp-gepetto-viewer_extra_flags= ${PYTHON_FLAGS} -DUSE_HPP_PYTHON=ON -DINSTALL_DOCUMENTATION=OFF

hpp-plot_branch=devel
hpp-plot_repository=${HPP_REPO}
hpp-plot_extra_flags=  -DINSTALL_DOCUMENTATION=OFF

# }}}
##################################
# {{{ Packages for hpp-plot

qgv_branch=devel
qgv_repository=${HPP_REPO}
qgv_extra_flags=-DBINDINGS_QT5=ON -DBINDINGS_QT4=OFF

# }}}
##################################
# {{{ Packages for toppra

toppra_repository=https://github.com/hungpham2511
toppra_branch=develop
toppra_extra_flags= -DBUILD_TESTS=OFF -DPYTHON_BINDINGS=OFF

hpp-toppra_repository=${HPP_REPO}
hpp-toppra_branch=main
hpp-toppra_extra_flags=

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
		python -m venv ${INSTALL_HPP_DIR}; \
		${INSTALL_HPP_DIR}/bin/pip install --prefix=${INSTALL_HPP_DIR} \
			"numpy==1.26.4" trimesh pycollada viser; \
	fi

# }}}
##################################
# {{{ Dependencies declaration

jrl-cmakemodules.configure.dep: jrl-cmakemodules.checkout
hpp-doc.configure.dep: hpp-doc.checkout
hpp-plot.configure.dep: hpp-plot.checkout jrl-cmakemodules.install qgv.install
hpp-python.configure.dep: hpp-python.checkout jrl-cmakemodules.install
qgv.configure.dep: qgv.checkout jrl-cmakemodules.install
hpp_tutorial.configure.dep: hpp_tutorial.checkout hpp-gepetto-viewer.install \
	hpp-python.install
hpp-gepetto-viewer.configure.dep: hpp-gepetto-viewer.checkout python-venv hpp-python.install
toppra.configure.dep: toppra.checkout
hpp-toppra.configure.dep: hpp-toppra.checkout jrl-cmakemodules.install toppra.install

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

%.checkout:
	if [ -d $(@:.checkout=) ]; then \
		echo "$(@:.checkout=) already checkout out."; \
	else \
		git clone ${GIT_QUIET} --recursive -b ${$(@:.checkout=)_branch} ${$(@:.checkout=)_repository}/$(@:.checkout=); \
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
		git checkout -q ${$(@:.update=)_branch};\
		git submodule update; \
	fi


%.configure.dep: %.checkout

%.configure: %.configure.dep
	${MAKE} $(@:.configure=).configure_nodep

%.configure_nodep:%.checkout
	mkdir -p ${SRC_DIR}/$(@:.configure_nodep=)/${BUILD_FOLDER}; \
	cd ${SRC_DIR}/$(@:.configure_nodep=)/${BUILD_FOLDER}; \
	cmake -DCMAKE_INSTALL_PREFIX=${INSTALL_HPP_DIR} -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_BUILD_TYPE=${BUILD_TYPE} \
			-DENFORCE_MINIMAL_CXX_STANDARD=ON \
			-DINSTALL_DOCUMENTATION=${INSTALL_DOCUMENTATION} \
			-DCMAKE_CXX_FLAGS_RELWITHDEBINFO="-g -O3 -DNDEBUG" \
			${CLANG_FLAGS} \
			${$(@:.configure_nodep=)_extra_flags} ..

%.install:%.configure
	${MAKE} -C ${SRC_DIR}/$(@:.install=)/${BUILD_FOLDER} install

%.install_nodep:%.configure_nodep
	${MAKE} -C ${SRC_DIR}/$(@:.install_nodep=)/${BUILD_FOLDER} install

%.uninstall:
	${MAKE} -C ${SRC_DIR}/$(@:.uninstall=)/${BUILD_FOLDER} uninstall

%.clean:
	${MAKE} -C ${SRC_DIR}/$(@:.clean=)/${BUILD_FOLDER} clean

%.very-clean:
	rm -rf ${SRC_DIR}/$(@:.very-clean=)/${BUILD_FOLDER}/*

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
	cmake -DCMAKE_INSTALL_PREFIX=${INSTALL_HPP_DIR} -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_BU\
ILD_TYPE=${BUILD_TYPE} \
                        -DENFORCE_MINIMAL_CXX_STANDARD=ON \
                        -DINSTALL_DOCUMENTATION=${INSTALL_DOCUMENTATION} \
                        -DCMAKE_CXX_FLAGS_RELWITHDEBINFO="-g -O3 -DNDEBUG" \
                        ${CLANG_FLAGS} \
                        ${$(@:.configure_nodep=)_extra_flags} ..

toppra.install:toppra.configure
	${MAKE} -C ${SRC_DIR}/$(@:.install=)/cpp/${BUILD_FOLDER} install

toppra.install_nodep:toppra.configure_nodep
	${MAKE} -C ${SRC_DIR}/$(@:.install_nodep=)/cpp/${BUILD_FOLDER} install
