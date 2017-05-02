#!/bin/bash

set -e

# PREFIX_DIR=darshan-3.1.2-$(git log | grep -m 1 commit | sed -e 's/^commit \(.......\).*/\1/')
PREFIX_DIR=darshan-3.1.4
BZIP2_DIR=/global/u2/g/glock/apps.cori-haswell/bzip2-1.0.6
ENABLE_SHARED=""
# ENABLE_SHARED="--enable-shared"

DARSHAN_HOME=$PWD

function gen_setenv_template() {
    if [ -z "$INSTALL_PATH" -o -z "$PREFIX_DIR" ]; then
        echo "Undefined INSTALL_PATH or PREFIX_DIR" >&2
        return 1
    fi
    echo "Installing setenv.sh into $INSTALL_PATH/$PREFIX_DIR"
    cat <<EOF > $INSTALL_PATH/$PREFIX_DIR/setenv.sh
    module use $INSTALL_PATH/$PREFIX_DIR/share/craype-2.x/modulefiles
    module unload darshan
    module load darshan/$(cut -d- -f2 <<< $PREFIX_DIR)
EOF
}


function build_edison() {
    module unload PrgEnv-intel PrgEnv-cray
    module load PrgEnv-gnu

    module unload darshan

    if [ ! -z "$PREFIX_DIR" -a -d "/global/homes/g/glock/apps.edison/$PREFIX_DIR" ]; then
        echo "Removing old install directory for $PREFIX_DIR"
        rm -rf "/global/homes/g/glock/apps.edison/$PREFIX_DIR"
    fi

    for build_dir in "$DARSHAN_HOME/darshan-runtime/build" "$DARSHAN_HOME/darshan-util/build"; do
        if [ -d "$build_dir" ]; then
            rm -rf "$build_dir"
        fi
        mkdir -pv "$build_dir"
    done

    INSTALL_PATH="$HOME/apps.edison"
    DARSHAN_RUNTIME_CONFIG_FLAGS="--enable-HDF5-pre-1.10 $ENABLE_SHARED --with-log-path-by-env=DARSHAN_LOGPATH,SLURM_SUBMIT_DIR,PWD --disable-cuserid --with-mem-align=8 --with-jobid-env=SLURM_JOBID --enable-mmap-logs CC=cc"
    DARSHAN_UTIL_CONFIG_FLAGS="--with-zlib --with-bzlib=$BZIP2_DIR $ENABLE_SHARED CC=cc"
    cd "$DARSHAN_HOME/darshan-runtime/build"
    make distclean || true
    ../configure --prefix=$INSTALL_PATH/$PREFIX_DIR $DARSHAN_RUNTIME_CONFIG_FLAGS
    make -j16
    make install
    cd "$DARSHAN_HOME/darshan-util/build"
    make distclean || true
    ../configure --prefix=$INSTALL_PATH/$PREFIX_DIR $DARSHAN_UTIL_CONFIG_FLAGS
    make -j16
    make install
    cd "$DARSHAN_HOME"

    gen_setenv_template
}

function build_cori() {
    module unload PrgEnv-intel PrgEnv-cray
    module load PrgEnv-gnu

    module unload darshan

    for build_dir in "$DARSHAN_HOME/darshan-runtime/build" "$DARSHAN_HOME/darshan-util/build"; do
        if [ -d "$build_dir" ]; then
            rm -rf "$build_dir"
        fi
        mkdir -pv "$build_dir"
    done

    DARSHAN_RUNTIME_CONFIG_FLAGS="--enable-HDF5-pre-1.10 $ENABLE_SHARED --with-log-path-by-env=DARSHAN_LOGPATH,SLURM_SUBMIT_DIR,PWD --disable-cuserid --with-mem-align=8 --with-jobid-env=SLURM_JOBID --enable-mmap-logs CC=cc"
    DARSHAN_UTIL_CONFIG_FLAGS="--with-zlib $ENABLE_SHARED --with-bzlib=$BZIP2_DIR CC=cc"

    for INSTALL_PATH in "$HOME/apps.cori-haswell" "$HOME/apps.cori-knl"
    do
        module unload craype-haswell craype-mic-knl
        module load craype-haswell
        ### or load craype-mic-knl, but for now, just build everything against Haswell

        if [ ! -z "$PREFIX_DIR" -a -d "$INSTALL_PATH/$PREFIX_DIR" ]; then
            echo "Removing old install directory $INSTALL_PATH/$PREFIX_DIR"
            rm -rf "$INSTALL_PATH/$PREFIX_DIR"
        fi

        cd "$DARSHAN_HOME/darshan-runtime/build"
        make distclean || true
        ../configure --prefix=$INSTALL_PATH/$PREFIX_DIR $DARSHAN_RUNTIME_CONFIG_FLAGS
        make -j16
        make install
        cd "$DARSHAN_HOME/darshan-util/build"
        make distclean || true
        ../configure --prefix=$INSTALL_PATH/$PREFIX_DIR $DARSHAN_UTIL_CONFIG_FLAGS
        make -j16
        make install
        cd "$DARSHAN_HOME"

        gen_setenv_template
    done

}

if [ "$NERSC_HOST" == "edison" ]; then
    build_edison
elif [ "$NERSC_HOST" == "cori" ]; then
    build_cori
fi
