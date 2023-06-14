#!/usr/bin/env python
#
#  Take the results of the following ElasticSearch query:
#
#    hostname:bb* AND collectd_type:pending_operations AND plugin_instance:nvme*
#
#  and organize the results into per-timestamp, per-bbn rows that display the
#  queue depths of each NVMe device.
#

import sys
import json
import pandas
import datetime

results = {}

### first parse the json and group data by timestamp-bbnode
for result in json.load(open(sys.argv[1], 'r'))['hits']['hits']:
    hit = result['_source']
    timestamp = datetime.datetime.strptime(hit['@timestamp'].split('.')[0], "%Y-%m-%dT%H:%M:%S")
    bb_nodenum = hit['hostname'].lstrip('b')
    key = "%s_%s" % (timestamp, hit['hostname'])
    if key not in results:
        results[key] = {
            'timestamp': timestamp,
            'hostname': hit['hostname'],
            'hostnumber': bb_nodenum,
        }
    nvme_device = hit['plugin_instance']
    results[key][nvme_device] = hit['value']

### convert the above json into something ingestible by pandas
dict_to_df = []
for _, values in results.iteritems():
    record = {}
    for key, value in values.iteritems():
        record[key] = value
    dict_to_df.append(record)

print pandas.DataFrame.from_dict(results, orient='index')\
    .sort_values(by=['timestamp', 'hostnumber'])\
    [['timestamp','hostname','nvme0n1','nvme1n1','nvme2n1','nvme3n1']]\
    .to_csv(index=False, header=True)
