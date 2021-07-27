'''
  Argus Data Platform (ADP) write API

  This API is to be used by applications that are developed using the ADP.

  Current status: Proposed API
  (Possible statuses: Reviewed | Experimental Use | Accepted)

  Expected usage:
    write_obj = WriteApi("172.12.23.2", 4242)
    write_obj.write_ts(timeseries_id, timestamp1, value1)
    ...
    write_obj.write_ts(timeseries_id2, timestamp2, value2)
    ...
    write_obj.write_ts(timeseries_id2, timestamp3, value3)
'''

import json
import requests
import sys
import syslog as log

from enum import Enum
from . import basic_types
from . import timeseries_id as ts_id

class WriteApi(object):
    def __init__(self, dest_ip_or_hostname, dest_port_num,
                 tsdb_platform=basic_types.Tsdb.OPENTSDB):
        if tsdb_platform == basic_types.Tsdb.OPENTSDB:
            write_api_http_end_point = "api/put"
        else:
            assert(False)
        self.__dest_url = 'http://%s:%d/%s' % \
                          (dest_ip_or_hostname, dest_port_num,
                                                write_api_http_end_point)

    def write_ts(self, ts_id, timestamp, value):
        headers = {'content-type': 'application/json'}
        datapoint = {}
        datapoint['metric'] = ts_id.metric_id
        datapoint['timestamp'] = timestamp
        datapoint['value'] = value
        datapoint['tags'] = {}
        datapoint['tags'] = { k:ts_id.filters[k] for k in ts_id.filters }

        response = None
        try:
            response = requests.post( \
                self.__dest_url, data=json.dumps(datapoint), headers=headers)
            # FIXME: Ensure test coverage for error paths before pulling a PR.
            if not response.ok:
                log.syslog(log.LOG_ERR,
                           "[Timeseries write error: %d] "
                           "Timeseries_id:%s Timestamp:%s Value:%s" %
                    (response.json()['error']['code'], str(ts_id),
                     str(timestamp), str(value)))

        except Exception:
            # FIXME: Ensure test coverage for error paths before pulling a PR.
            exc_type, value, traceback = sys.exc_info()
            log.syslog(log.LOG_ERR,
                       "[Timeseries write POST exception: %s] "
                       "Timeseries_id:%s Timestamp:%s Value:%s" %
                       (exc_type.__name__, str(ts_id), str(timestamp),
                       str(value)))

        return response
