#!/usr/bin/env bash
#
#  Tool for archiving H5LMT data
#

FS_NAME=${1}
H5LMT_DIR=${2-/global/project/projectdirs/pma/www/daily}
SCRATCH_DIR=$SCRATCH

if [ -z "$FS_NAME" ]; then
    echo "Syntax: $0 <snx11025|snx11035|snx11036|snx11168|...>"
    exit 1
elif [ ! -d "$H5LMT_DIR" ]; then
    echo "Cannot find H5LMT data dir $H5LMT_DIR" >&2
    exit 1
fi

cd "$H5LMT_DIR"

for yr in $(seq 2011 $(date +%Y))
do
    for month in $(seq 1 12)
    do
        log_dir="./$yr-$(printf "%02d" $month)-*"

        ### if the month is incomplete, don't bother trying to archive it
        if [ "$yr" -ge "$(date +%Y)" -a "$month" -ge "$(date +%m)" ]
        then
            echo "Stopping at $log_dir since it is in the future!"
            break
        fi

        ### don't try to overwrite existing archives
        tarfile=$(printf "h5lmt_%s_%d-%02d.tar.gz" "$FS_NAME" "$yr" "$month")
        if hsi ls "$tarfile" >/dev/null 2>&1
        then
            echo "$tarfile already exists; skipping"
            continue
        fi

        ### don't create empty tarfiles
        file_ct=$(find $log_dir -type f -name \*${FS_NAME}.h5lmt | wc -l)
        if [ $file_ct -le 0 ]
        then
            echo "No files found in $log_dir; skipping" >&2
            continue
        fi

        ### pull the trigger and make the tarfile
        echo "Found $file_ct files in $log_dir"
        failures=0
        shopt -s globstar
        for i in $log_dir/*${FS_NAME}.h5lmt $log_dir/${FS_NAME}.hdf5
        do
            ### will match on 2017-01-01/cori_snx11168.h5lmt
            date=$(dirname "$i" | cut -d "/" -f2)
            bn=$(basename $i .h5lmt)
            new_name="${bn}-${date}.h5lmt"
            ### -vuf = verbose, update, file=.  Can't gzip inline because of -u
            tar -vuf "$SCRATCH_DIR/$(basename $tarfile .gz)" "${i}" --transform="s|${i}|${new_name}|"
            if [ $? -ne 0 ]; then
                let "failures++"
            fi
        done
        if [ $failures -gt 0 ]; then
            echo "WARNING: detected $failures failures" >&2
        fi
        gzip -v -9 "$SCRATCH_DIR/$(basename ${tarfile} .gz)"
        hsi put "$SCRATCH_DIR/${tarfile}" : "${tarfile}" && rm -v "$SCRATCH_DIR/${tarfile}"
    done
done
