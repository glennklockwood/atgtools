#!/usr/bin/env bash
#
#  Tool for archiving Darshan logs
#

DARSHAN_DIR=${1-$SCRATCH/../darshanlogs}
NERSC_HOST=${NERSC_HOST-$HOST}
SCRATCH_DIR=$SCRATCH

if [ ! -d "$DARSHAN_DIR" ]; then
    echo "Cannot find Darshan logs dir $DARSHAN_DIR" >&2
    exit 1
fi

cd "$DARSHAN_DIR"

for yr in $(seq 2014 $(date +%Y))
do
    for month in $(seq 1 12)
    do
        log_dir="./$yr/$month"

        ### if the month is incomplete, don't bother trying to archive it
        if [ "$yr" -ge "$(date +%Y)" -a "$month" -ge "$(date +%m)" ]
        then
            echo "Stopping at $log_dir since it is in the future!"
            break
        fi

        ### don't try to overwrite existing archives
        tarfile=$(printf "darshan_logs_%s-%d-%02d.tar" "$NERSC_HOST" "$yr" "$month")
        if hsi ls "$tarfile" >/dev/null 2>&1
        then
            echo "$tarfile already exists; skipping"
            continue
        fi

        ### don't create empty tarfiles
        file_ct=$(find $log_dir -type f ! -name . -prune -print | grep -c '/')
        if [ $file_ct -le 0 ]
        then
            echo "No files found in $log_dir; skipping" >&2
            continue
        fi

        ### pull the trigger and make the tarfile
        echo "Found $file_ct files in $log_dir"
        # htar -Hcrc -cvf $tarfile $log_dir
        tar -cvf $SCRATCH_DIR/$tarfile $log_dir && hsi put "$SCRATCH_DIR/$tarfile" && rm -v $SCRATCH_DIR/$tarfile
    done
done
