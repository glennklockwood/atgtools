#!/usr/bin/env python
"""
Parses the stdout of one or more IOR invocations
"""
import sys
import datetime
import re
import json

def un_human_readable( value_str ):
    """
    Takes the output of IOR's HumanReadable() and converts it back to a byte
    value
    """
    args = value_str.strip().split()
    if len(args) == 1 and args[0].endswith("%"):
        return float(args[0].rstrip("%"))
    elif len(args) != 2:
        raise Exception("Invalid input string[%s]" % value_str)

    value = float(args[0])
    unit = args[1]
    if unit == "-":
        mult = 1.0
    elif unit == "bytes":
        mult = 1.0
    elif unit == "MiB":
        mult = 2.0**20
    elif unit == "GiB":
        mult = 2.0**30
    elif unit == "MB":
        mult = 10.0**6.0
    elif unit == "GB":
        mult = 10.0**9.0
    elif unit == "TiB": # from ShowFileSystemSize()
        mult = 2.0**40
    elif unit == "Mi":
        mult = 2.0**20
    else:
        raise Exception("Unknown value_str " + value_str)
    return value * mult

def parse( ior_output ):
    """
    input: a list of file names containing IOR's stdout messages
    output: tuple containing
        1. list of h5lmt file names corresponding to input files
        2. subset of input that was used to generate output #1
    """
    data = { }

    section = None
    for line in ior_output:
        if line.startswith("Run began"):
            data['start'] = datetime.datetime.strptime(line.split(':',1)[1].strip(), "%c")
        elif line.startswith('Path'):
            data['path'] = line.split()[1]
        elif line.startswith("Run finished"):
            data['stop'] = datetime.datetime.strptime(line.split(':',1)[1].strip(), "%c")
            ### don't proceed, just in case there is another concatenated output
            ### on the same iterable
            break
        elif line.startswith("FS:"):
            data['file_system'] = {}
            for fsfield in [ x.strip() for x in line.split("  ") ]:
                key, value = [ x.strip() for x in fsfield.split(":") ]
                value = un_human_readable(value)
                ### these conversions lose precision due to the way IOR prints
                ### values
                if fsfield.startswith('FS:'):
                    data['file_system']['approx_total_bytes'] = long(value)
                elif fsfield.startswith('Used FS:'):
                    data['file_system']['approx_used_bytes_pct'] = value
                elif fsfield.startswith('Inodes:'):
                    data['file_system']['approx_total_inodes'] = long(value)
                elif fsfield.startswith('Used Inodes:'):
                    data['file_system']['approx_used_inodes_pct'] = value
        elif section is None and line.strip() == "Summary:":
            section = 'summary'
            data['summary'] = {}
        elif section == 'summary' and line.strip() == "":
            section = None
        elif section == 'summary':
            key, val = line.split('=')
            key = key.strip()
            val = val.strip()
            key = key.replace(' ', '_')
            if key == 'clients':
                rex_match = re.match('(\d+) \((\d+) per node', val)
                if rex_match is not None:
                    val = int(rex_match.group(1))
                    data['summary']['ppn'] = int(rex_match.group(2))
            elif key == 'pattern':
                rex_match = re.match('(\S+)\s+\((\d+) segments', val)
                if rex_match is not None:
                    val = rex_match.group(1)
                    data['summary']['segments'] = int(rex_match.group(2))
            elif key == 'repetitions':
                val = int(val)
            elif (key == 'xfersize'
               or key == 'blocksize'
               or key == 'aggregate_filesize'):
                val = un_human_readable(val)
            data['summary'][key] = val
    return data

if __name__ == '__main__':
    data = parse(open(sys.argv[1], 'r'))
    if 'start' in data:
        data['start'] = str(data['start'])
    if 'stop' in data:
        data['stop'] = str(data['stop'])
    print json.dumps(data, indent=4, sort_keys=True)
