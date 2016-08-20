#!/usr/bin/env python
#
#  Comb through the ALTD database to find all recorded jobs that do and do not
#  use executables that linked against Darshan.
#
#  Includes a --custom mode for use on databases where both ALTD tables and the
#  jobs table are present.  This is not how production is set up, but you can
#  create your own private database and copy both sets of tables there.  This
#  allows correlation between ALTD job ids and actual job info.
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
    COUNT(*)
FROM ( %(all_altds_query)s ) as a;
'''

_ALL_ALTDS_QUERY = """
SELECT DISTINCT
    concat(job_launch_id, '.edique02') AS jobid
FROM
    (
        SELECT
            tag_id AS abc,
            job_launch_id
        FROM
            altd_edison_jobs AS jobs
        WHERE
            jobs.run_date >= '%(date_start)s'
        AND jobs.run_date < '%(date_stop)s'
    ) AS filtered_jobs
INNER JOIN altd_edison_link_tags AS tags ON tags.tag_id = filtered_jobs.abc
INNER JOIN (
    SELECT
        linking_inc
    FROM
        altd_edison_linkline AS linklines
    %(linkline_filter_str)s
) AS filtered_linklines ON tags.linkline_id = filtered_linklines.linking_inc
"""

_ALL_JOBS_QUERY = """
SELECT
    stepid,
    s.numnodes * s.wallclock / 3600.0 AS cycles
FROM
    summary AS s
WHERE
    hostname = 'edison'
AND s.`completion` >= UNIX_TIMESTAMP('%(date_start)s 00:00:00')
AND s.`completion` < UNIX_TIMESTAMP('%(date_stop)s 00:00:00')
"""

_ALTD_AND_JOBS_COUNT_QUERY = """
SELECT
     count(*), sum(cycles)
FROM ( %(all_jobs_query)s) AS a
%(join_type)s JOIN ( %(all_altds_query)s ) AS b ON a.stepid = b.jobid
"""

def craft_all_jobs_query( date_start, date_stop ):
    """
    Query to return a a list of all jobs in the jobs database
    """
    return _ALL_JOBS_QUERY % {
        "date_start": date_start.strftime(_DATE_FMT),
        "date_stop": date_stop.strftime(_DATE_FMT),
    }

def craft_all_jobs_count_query( date_start, date_stop ):
    return "SELECT COUNT(*), SUM(cycles) from ( %s ) as a" % craft_all_jobs_query(date_start, date_stop)

def craft_altd_and_jobs_count_query( date_start, date_stop, include_jobs=True, include_altds=True, include_libs=[], exclude_libs=[] ):
    if include_jobs and include_altds:
        ### inner join will only return jobs with matching ALTDs
        query_str = _ALTD_AND_JOBS_COUNT_QUERY % {
            "join_type" : "INNER",
            "all_jobs_query" : craft_all_jobs_query( date_start, date_stop ),
            "all_altds_query" : craft_all_altds_query( date_start, date_stop, include_libs, exclude_libs ),
        }
    elif not include_jobs and include_altds:
        ### right join will include all ALTDs
        query_str = _ALTD_AND_JOBS_COUNT_QUERY % {
            "join_type" : "RIGHT",
            "all_jobs_query" : craft_all_jobs_query( date_start, date_stop ),
            "all_altds_query" : craft_all_altds_query( date_start, date_stop, include_libs, exclude_libs ),
        }
        ### filtering for NULL finds altds that have no corresponding jobs
        query_str = query_str + '\nWHERE jobid IS NULL OR stepid IS NULL'
    elif include_jobs and not include_altds:
        ### left join will include all jobs
        query_str = _ALTD_AND_JOBS_COUNT_QUERY % {
            "join_type" : "LEFT",
            "all_jobs_query" : craft_all_jobs_query( date_start, date_stop ),
            "all_altds_query" : craft_all_altds_query( date_start, date_stop, include_libs, exclude_libs ),
        }
        ### filtering for NULL finds jobs that have no corresponding ALTDs
        query_str = query_str + '\nWHERE jobid IS NULL OR stepid IS NULL'
    else:
        raise Exception('excluding jobs and altds will return nothing')

    print query_str
    return query_str

def craft_altd_count_query( date_start, date_stop, include=[], exclude=[] ):
    """
    Query to return just a total count of ALTD jobs that include/exclude
    certain libraries
    """
    return _ALTD_COUNT_QUERY % { 
        'all_altds_query': craft_all_altds_query( date_start, date_stop, include, exclude )
    }

def craft_all_altds_query( date_start, date_stop, include=[], exclude=[] ):
    """
    Query to return a list of all ALTD jobids that include/exclude certain
    libraries
    """
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

    return _ALL_ALTDS_QUERY % {
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
    parser.add_argument( '--custom', '-c', action='store_true')
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

    if args.custom:
        analysis_custom_db( date_start, date_stop, cursor )
    else:
        analysis_only_altd( date_start, date_stop, cursor )

def analysis_custom_db( date_start, date_stop, cursor ):
    ### begin looping over months and calculate coverage
    field_names = [
        "start",
        "total jobs",
        "altd jobs",
        "non-altd jobs",
        "darshan mpi jobs",
        "non-darshan mpi jobs",
        "darshan non-mpi jobs",
        "non-darshan non-mpi jobs",
        "jobs in altd but not db",
        "total cycles",
        "altd cycles",
        "non-altd cycles",
        "darshan mpi cycles",
        "non-darshan mpi cycles",
        "darshan non-mpi cycles",
        "non-darshan non-mpi cycles"
    ]
    print ','.join(field_names)

    fmt_string = ",".join( [ r'%(' + x + r')s,' for x in field_names ] )
    fmt_string.rstrip(',')

    t = date_start
    while t < date_stop:
        t0 = t
        tf = t0 + dateutil.relativedelta.relativedelta(months=1)
        output = { 'start' : t0.strftime(_DATE_FMT) }

        ### total jobs, total cycles
        query_str = craft_all_jobs_count_query( t0, tf )
        cursor.execute( query_str )
        rows = cursor.fetchall()
        output['total jobs'] = str(rows[0][0])
        output['total cycles'] = str(rows[0][1])

        ### altd jobs, altd cycles
        query_str = craft_altd_and_jobs_count_query( 
                        date_start,
                        date_stop,
                        include_jobs=True,
                        include_altds=True,
                        include_libs=[],
                        exclude_libs=[] )
        cursor.execute( query_str )
        rows = cursor.fetchall()
        output['altd jobs'] = str(rows[0][0])
        output['altd cycles'] = str(rows[0][1])

        ### non-altd jobs, non-altd cycles
        query_str = craft_altd_and_jobs_count_query( 
                        date_start,
                        date_stop,
                        include_jobs=True,
                        include_altds=False,
                        include_libs=[],
                        exclude_libs=[] )
        cursor.execute( query_str )
        rows = cursor.fetchall()
        output['non-altd jobs'] = str(rows[0][0])
        output['non-altd cycles'] = str(rows[0][1])

        ### darshan mpi jobs
        query_str = craft_altd_and_jobs_count_query( 
                        date_start,
                        date_stop,
                        include_jobs=True,
                        include_altds=True,
                        include_libs=[ "darshan", "mpi" ],
                        exclude_libs=[] )
        cursor.execute( query_str )
        rows = cursor.fetchall()
        output['darshan mpi jobs'] = str(rows[0][0])
        output['darshan mpi cycles'] = str(rows[0][1])

        ### non-darshan mpi jobs
        query_str = craft_altd_and_jobs_count_query( 
                        date_start,
                        date_stop,
                        include_jobs=True,
                        include_altds=True,
                        include_libs=[ "mpi" ],
                        exclude_libs=[ "darshan" ] )
        cursor.execute( query_str )
        rows = cursor.fetchall()
        output['non-darshan mpi jobs'] = str(rows[0][0])
        output['non-darshan mpi cycles'] = str(rows[0][1])

        ### darshan non-mpi jobs (this shouldn't be possible since darshan links in mpi...)
        query_str = craft_altd_and_jobs_count_query( 
                        date_start,
                        date_stop,
                        include_jobs=True,
                        include_altds=True,
                        include_libs=[ "darshan" ],
                        exclude_libs=[ "mpi" ] )
        cursor.execute( query_str )
        rows = cursor.fetchall()
        output['darshan non-mpi jobs'] = str(rows[0][0])
        output['darshan non-mpi cycles'] = str(rows[0][1])

        ### non-darshan non-mpi jobs
        query_str = craft_altd_and_jobs_count_query( 
                        date_start,
                        date_stop,
                        include_jobs=True,
                        include_altds=True,
                        include_libs=[],
                        exclude_libs=[ "darshan", "mpi" ] )
        cursor.execute( query_str )
        rows = cursor.fetchall()
        output['non-darshan non-mpi jobs'] = str(rows[0][0])
        output['non-darshan non-mpi cycles'] = str(rows[0][1])

        ### Weird jobs that are in altd but not the jobs db; this shouldn't
        ### ever happen.  Can't get cycles because there's no record in the
        ### jobs database
        query_str = craft_altd_and_jobs_count_query( 
                        date_start,
                        date_stop,
                        include_jobs=False,
                        include_altds=True,
                        include_libs=[],
                        exclude_libs=[] )
        cursor.execute( query_str )
        rows = cursor.fetchall()
        output['jobs in altd but not db'] = str(rows[0][0])

        print ",".join( [ output[x] for x in field_names ] )
       
        t = tf


def analysis_only_altd( date_start, date_stop, cursor ):
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

        ### jobs without darshan (but with MPI)
        query_str = craft_altd_count_query( t0, tf, include=['mpi'], exclude=['darshan'] )
        cursor.execute( query_str )
        rows = cursor.fetchall()
        without_darshan = rows[0][0]
       
        print "%12s %12s %10ld %10ld" % (
            t0.strftime(_DATE_FMT),
            tf.strftime(_DATE_FMT),
            with_darshan,
            without_darshan )

        t = tf

if __name__ == '__main__':
    main()
