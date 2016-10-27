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
import hashlib

ANONYMIZE_SN = True

def anonymize_sn( sn ):
    """
    Anonymize the serial number of each device, but preserve its enumerated id
    (0 or 1 for Intel DC P3608)
    """
    if ANONYMIZE_SN:
        sn, devid = sn.split('-',1)
        hash = hashlib.md5()
        hash.update(sn)
        return (hash.hexdigest() + "-" + devid).strip()
    else:
        return sn

def load_dev_map( path ):
    """
    Load map containing serial numbers and node names.  Each line in this device
    map file should have a format

        CVF000000000000000-1 nid00000

    with the device serial number, a space, and the node to which it belongs
    """
    dev_map = {}
    if path is None:
        warnings.warn("Unable to load device map file")
        return dev_map
    try:
        with open( path, 'r' ) as fp:
            for line in fp:
                sn, node = line.split(None, 1)
                sn = anonymize_sn( sn )
                dev_map[sn] = node.strip()
    except IOError:
        warnings.warn("Unable to load device map file")
        pass
    return dev_map

def rekey_smart_buffer(smart_buffer):
    """
    Take a buffer containing smart values associated with one register and
    create unique counters
    """
    data = {}
    prefix = smart_buffer.get("Description")
    if prefix is None:
        prefix = smart_buffer.get("_id")

    for key, val in smart_buffer.iteritems():
        key = ("%s_%s" % (prefix, key.strip())).replace("-","").replace(" ", "_")
        data[key] = val.strip()
    return data

def parse_dct_counters_file( path, dev_map=None ):
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
    smart_buffer = {}
    with open( path, 'r' ) as fp:
        for line in fp:
            line = line.strip()
            if device_sn is None:
                rex_match = re.search( '(Intel SSD|SMART Attributes).*(CVF[^ ]+-\d+)', line )
                if rex_match is not None:
                    device_sn = anonymize_sn(rex_match.group(2))
                    if device_sn in dev_map:
                        data['NodeName'] = dev_map[device_sn]
                    else:
                        data['NodeName'] = "unknown"
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
                key, val = line.split(':')
                smart_buffer[key.strip()] = val.strip()
            elif parse_mode > 0 and line.startswith('-') and line.endswith('-'):
                for key, val in rekey_smart_buffer(smart_buffer).iteritems():
                    data[key.strip()] = val
                smart_buffer = { '_id' : line.split()[1] }
        if parse_mode > 0: # flush the last SMART register
            for key, val in rekey_smart_buffer(smart_buffer).iteritems():
                data[key] = val

    if device_sn is None:
        warnings.warn("Couldn't find device sn in " + path)
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

def parse_many_dct_counters_files( file_list, dev_map_file=None ):
    """
    Receives a list of file paths and parses all input files.  The counters
    from each file are aggregated based on the NVMe device serial number, with
    redundant counters being overwritten.
    
    Returns a dict of dicts containing all counters keyed by serial number.
    """

    dev_map = load_dev_map(dev_map_file)

    all_data = {}
    for f in file_list:
        parsed_counters = parse_dct_counters_file(f, dev_map)
        if parsed_counters is None:
            warnings.warn("No valid counters found in " + f)
            continue
        elif len(parsed_counters.keys()) > 1:
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
            ### first, handle counters that do not have an obvious way to cast
            if counter in ("Temperature", "Thermal_Throttle_Status_ThrottleStatus"):
                value = value.split()[0]

            ### the order here is important, but hex that is not prefixed with
            ### 0x may be misinterpreted as integers.  if such counters ever
            ### surface, they must be explicitly cast above
            for cast in ( long, float, lambda x: long(x,16) ):
                try:
                    new_value = cast(value)
                    break
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
    """
    Transforms the data from either parse_dct_counters_file or
    parse_many_dct_counters_files into a dataframe with only the numeric columns
    extracted.  All non-numeric columns are dropped except for node name
    """
    df = pandas.DataFrame.from_dict(input_dict, orient='index')
    numeric_df = df.apply(pandas.to_numeric, errors='coerce')
    numeric_keys = []
    for i in sorted(df.keys()):
        ### don't print counters that are non-numeric
        if df[i].dtype != np.int64 and df[i].dtype != np.float64:
            continue

        ### don't print counters that are the same for all devices. df.count > 1
        ### because we can't tell how many rows are unique if there's only one
        ### row
        if df.shape[0] > 1 and len(df[i].unique()) == 1:
            continue

        numeric_keys.append( i )

    if 'NodeName' in df:
        numeric_keys = [ 'NodeName' ] + numeric_keys
    return df[numeric_keys]

if __name__ == '__main__':
    all_data = parse_many_dct_counters_files( sys.argv[1:], 'dev_map.txt' )
    df = counters_dict_to_numeric_dataframe( all_data )
    df.index.name = "DeviceID"
    print df.to_csv()
