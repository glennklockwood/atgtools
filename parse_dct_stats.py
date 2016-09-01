#!/usr/bin/env python
#
#  Tools to parse the flat-file formatted output from Intel DCT.  Returns a CSV
#  containing all of the numeric counters keyed by device serial number.
#
#  Downstream analysis of this CSV is demonstrated in analyze_dct_stats.ipynb
#  which should be included in this repository.
#
#

import os
import re
import sys
import pandas
import numpy as np
import warnings

def parse_dct_counters_file( path ):
    """Read the output of a single isdct command.  Understands the output of
    the following options:
      isdct show -smart (SMART attributes)
      isdct show -sensor (device health sensors)
      isdct show -performance (device performance metrics)
      isdct show -a (drive info)
    Outputs a dict of dicts keyed by the device serial number.
    """
    data = {}
    device_sn = None
    parse_mode = 0      # =0 for regular counters, >1 for SMART data
    counter_prefix = "" # for SMART data
    with open( path, 'r' ) as fp:
        for line in fp:
            if device_sn is None:
                rex_match = re.search( '(Intel SSD|SMART Attributes).*(CVF[^ ]+-\d+)', line )
                if rex_match is not None:
                    device_sn = rex_match.group(2)
                    if rex_match.group(1) == "Intel SSD":
                        parse_mode = 0
                    elif rex_match.group(1) == "SMART Attributes":
                        parse_mode = 1
                    else:
                        raise Exception("Unknown counter file format")
            elif parse_mode == 0 and ':' in line:
                key, val = line.split(':')
                data[key.strip()] = val.strip()
            elif parse_mode > 0 and ':' in line:
                if line.startswith('Description'):
                    counter_prefix = line.split(None, 2)[2].strip()
                    parse_mode += 1
                else:
                    key, val = line.split(':')
                    key = ( "%s_%s" % ( counter_prefix, key.strip() ) ).replace(" ", "_")
                    data[key] = val.strip()

    if device_sn is None:
        warnings.warn("Couldn't find device sn")
    else:
        return { device_sn : data }

def find_duplicate_keys( data_list ):
    """
    Return a list of key,value tuples of duplicate counters.  assumes data_list
    refers to a list of dicts that all have the same top-level key (the NVMe
    device serial number)
    """
    key = data_list[0].keys()[0]
    all_counters = set(data_list[0][key].keys())
    duplicates = set([])
    duplicate_kv = []
    for i in range(len(data_list)-1):
        duplicates = duplicates | ( all_counters & set(data_list[i+1][key].keys()) )
        all_counters = all_counters | set(data_list[i+1][key].keys())

    for i in data_list:
        for j in duplicates:
            if j in i[key]:
                duplicate_kv.append( (j, i[key][j]) )

    return duplicate_kv

def parse_many_dct_counters_files( file_list ):
    """Receives a list of file paths and parses all input files.  The counters
    from each file are aggregated based on the NVMe device serial number, with
    redundant counters being overwritten.
    
    Returns a dict of dicts containing all counters keyed by serial number."""

    all_data = {}
    for f in file_list:
        parsed_counters = parse_dct_counters_file(f)
        if len(parsed_counters.keys()) > 1:
            raise Exception("Received multiple serial numbers from parse_dct_counters_file")
        else:
            device_sn = parsed_counters.keys()[0] 
        ### merge file's counter dict with any previous counters we've parsed
        if device_sn not in all_data:
            all_data[device_sn] = parsed_counters[device_sn]
        else:
            all_data[device_sn].update(parsed_counters[device_sn])

    ### attempt to figure out the type of each counter
    for device_sn, counters in all_data.iteritems():
        for counter, value in counters.iteritems():
            new_value = None
            try:
                new_value = long(value)
            except ValueError:
                pass
            try:
                new_value = float(value)
            except ValueError:
                pass
            try:
                new_value = long(value, 16)
            except ValueError:
                pass
            if value == "True":
                new_value = True
            elif value == "False":
                new_value = False
            if new_value is not None:
                all_data[device_sn][counter] = new_value

    return all_data

def counters_dict_to_numeric_dataframe( input_dict ):
    """Transforms the data from either parse_dct_counters_file or
    parse_many_dct_counters_files into a dataframe with only the numeric
    columns extracted.  All non-numeric columns are dropped."""
    df = pandas.DataFrame.from_dict(input_dict, orient='index') \
                         .apply(pandas.to_numeric, errors='coerce')
    numeric_keys = []
    for i in df:
        if len(df[i].nonzero()[0]) == 0:
            continue
        if df[i].dtype != np.int64 and df[i].dtype != np.float64:
            continue
        if len(df[i].unique()) == 1:
            continue
        numeric_keys.append( i )

    return df[numeric_keys]

if __name__ == '__main__':
    all_data = parse_many_dct_counters_files( sys.argv[1:] )
    df = counters_dict_to_numeric_dataframe( all_data )
    print df.to_csv()
