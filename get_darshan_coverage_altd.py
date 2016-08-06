#!/usr/bin/env python
#
#  Comb through the ALTD database to find all recorded jobs that do and do not
#  use executables that linked against Darshan.
#
#  Glenn K. Lockwood, Lawrence Berkeley National Laboratory         August 2016

import re
import os
import sys
import argparse
import MySQLdb
import datetime
import dateutil.relativedelta

_DATE_FMT = "%Y-%m-%d"
_ALTD_COUNT_QUERY = '''
SELECT
    count(*)
FROM
    (
        SELECT
            tag_id
        FROM
            altd_edison_jobs AS jobs
        WHERE
            jobs.run_date >= '%(date_start)s'
        AND jobs.run_date < '%(date_stop)s'
    ) AS filtered_jobs
INNER JOIN altd_edison_link_tags AS tags ON tags.tag_id = filtered_jobs.tag_id
INNER JOIN (
    SELECT
        linking_inc
    FROM
        altd_edison_linkline AS linklines
    %(linkline_filter_str)s
) AS filtered_linklines ON tags.linkline_id = filtered_linklines.linking_inc;
'''

def craft_altd_count_query( date_start, date_stop, include=[], exclude=[] ):
    if len(include) + len(exclude) > 0:
        linkline_filter_str = "WHERE\n"
        i = 0
        for x in include:
            if i == 0:
                linkline_filter_str += "        "
            else:
                linkline_filter_str += "    AND "
            linkline_filter_str += "linklines.linkline LIKE '%%%s%%'\n" % x
            i += 1
        for x in exclude:
            if i == 0:
                linkline_filter_str += "        "
            else:
                linkline_filter_str += "    AND "
            linkline_filter_str += "linklines.linkline NOT LIKE '%%%s%%'\n" % x
            i += 1
    else:
        linkline_filter_str = ""

    return _ALTD_COUNT_QUERY % {
            "linkline_filter_str": linkline_filter_str,
            "date_start": date_start.strftime(_DATE_FMT),
            "date_stop": date_stop.strftime(_DATE_FMT),
        }

def str_to_date( date_str ):
    dt = datetime.datetime.strptime( date_str, _DATE_FMT )
    return datetime.date( year=dt.year, month=dt.month, day=dt.day )

def main():
    ### Parse command line parameters
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument( 'startdate',
        type=str,
        help='lower bound of dates to scan in %s format' % _DATE_FMT.replace(r'%',r'%%') )
    parser.add_argument( 'stopdate',
        type=str,
        help='upper bound of dates to scan in %s format' % _DATE_FMT.replace(r'%',r'%%') )
    parser.add_argument( '--host', '-h', type=str, default=os.environ.get('ALTD_HOST'))
    parser.add_argument( '--user', '-u', type=str, default=os.environ.get('ALTD_USER'))
    parser.add_argument( '--password', '-P', type=str, default=os.environ.get('ALTD_PASSWORD'))
    parser.add_argument( '--db', '-d', type=str, default=os.environ.get('ALTD_DB'))
    args = parser.parse_args()
    if not (args.startdate and args.stopdate):
        parser.print_help()
        sys.exit(1)

    if args.password is None:
        args.password = ""          ### allow empty passwords
    if args.host is None or args.user is None or args.password is None or args.db is None:
        parser.print_help()
        sys.stderr.write( """
ALTD host, login username and password, and database name must all be
specified either through command-line parameters or environment variables
(ALTD_HOST, ALTD_USER, ALTD_PASSWORD, ALTD_DB)\n""")
        sys.exit(1)

    ### convert input dates to date objects
    date_start = str_to_date( args.startdate )
    date_stop = str_to_date( args.stopdate )

    ### connect to the ALTD database
    db = MySQLdb.connect( 
        host=args.host,
        user=args.user,
        passwd=args.password,
        db=args.db )
    cursor = db.cursor()

    ### begin looping over months and calculate coverage
    print "%12s %12s %10s %10s" % ( "start", "end", "w/ darshan", "no darshan" )
    t = date_start
    while t < date_stop:
        t0 = t
        tf = t0 + dateutil.relativedelta.relativedelta(months=1)

        ### jobs with darshan
        query_str = craft_altd_count_query( t0, tf, include=['darshan','mpi'] )
        cursor.execute( query_str )
        rows = cursor.fetchall()
        with_darshan = rows[0][0]
        ### check for v10 style--this is really annoying because v10 style tags
        ### can be in non-v10 tables, meaning every query has to be run multiple
        ### times to check for different combinations of v10 and non-v10
        ### nomenclature.  NERSC upgraded from v10 in mid-2014, so as long as we
        ### don't loop over dates going back that far, sticking to the non-v10
        ### tables should be sufficient.
#       cursor.execute( re.sub(r'altd_edison_(\S+)', r'altd_edison_\1_v10', query_str) )
#       rows = cursor.fetchall()
#       with_darshan += rows[0][0]

        ### jobs without darshan (but with MPI)
        query_str = craft_altd_count_query( t0, tf, include=['mpi'], exclude=['darshan'] )
        cursor.execute( query_str )
        rows = cursor.fetchall()
        without_darshan = rows[0][0]
        ### check for v10 style
#       cursor.execute( re.sub(r'altd_edison_(\S+)', r'altd_edison_\1_v10', query_str) )
#       rows = cursor.fetchall()
#       with_darshan += rows[0][0]
       
        print "%12s %12s %10ld %10ld" % (
            t0.strftime(_DATE_FMT),
            tf.strftime(_DATE_FMT),
            with_darshan,
            without_darshan )

        t = tf

if __name__ == '__main__':
    main()
