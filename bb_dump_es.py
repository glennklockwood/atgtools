#!/usr/bin/env python
"""
Dump a lot of data out of ElasticSearch using the Python API and native
scrolling support
"""

import copy
import json
import gzip
import datetime

import elasticsearch
import elasticsearch.helpers

_QUERY_OST_DATA = {
    "query": {
        "bool": {
            "must": {
                "query_string": {
#                   "query": "hostname:bb* AND plugin:disk AND plugin_instance:nvme* AND collectd_type:disk_octets",
                    "query": "hostname:bb*",
                    "analyze_wildcard": True,
                },
            },
        },
    },
}
_SOURCE_FIELDS = [
    '@timestamp',
    'hostname',
    'plugin',
    'collectd_type',
    'type_instance',
    'plugin_instance',
    'value',
    'longterm',
    'midterm',
    'shortterm',
    'majflt',
    'minflt',
    'if_octets',
    'if_packets',
    'if_errors',
    'rx',
    'tx',
    'read',
    'write',
    'io_time',
]


t_start = datetime.datetime(2017, 4, 14, 19, 00, 00)
t_stop = datetime.datetime(2017, 4, 14, 19, 01, 00)

esdb = elasticsearch.Elasticsearch([{
    'host': 'localhost',
    'port': 9200, }])

query = copy.deepcopy( _QUERY_OST_DATA )

### Create the appropriate timeseries filter if it doesn't exist
this_node = query
for node_name in 'query', 'bool', 'filter', 'range', '@timestamp':
    if node_name not in this_node:
        this_node[node_name] = {}
    this_node = this_node[node_name]
### Update the timeseries filter
this_node['gte'] = t_start.strftime("%s")
this_node['lt'] = t_stop.strftime("%s")
this_node['format'] = "epoch_second"

### Print query
print json.dumps(query,indent=4)


### Get first set of results and a scroll id
result = esdb.search(
    index='cori-collectd-*',
    body=query,
    scroll='1m',
    size=10000,
    _source=_SOURCE_FIELDS,
)

### Keep scrolling until we have all the data
num_blob = 0
while len(result['hits']['hits']) > 0:
    sid = result['_scroll_id']

    print "Allegedly got %d hits" % result['hits']['total']
    print "Actually got %d hits" % len(result['hits']['hits'])
    i = 0
    index = result['hits']['hits'][i]['_index']
    source = result['hits']['hits'][i]['_source']
    print index, json.dumps(source,indent=4)
    output_file = "%s.%08d.json.gz" % (index, num_blob)
    with gzip.open( filename=output_file, mode='w', compresslevel=1 ) as fp:
        json.dump(result, fp)
        print "wrote", output_file

    result = esdb.scroll(scroll_id=sid, scroll='1m')
    num_blob += 1
