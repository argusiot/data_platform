'''
  query_urlgen.py

  Generates URLs for queries given all the query paramaters and TSDB type.

  This is a simple stateless module containing only functions to transform
  input to output.

  See README.opentsdb_query_reponse_samples for detailed on query types and
  sample output.
'''

from . import basic_types as bt

# collection of URL templates for constructing TSDB specific URLs.
tsdb_queryurl_templates = {
  bt.Tsdb.OPENTSDB: {
    'base_url': "http://%s:%d/api/query?start=%s&end=%s",
    'base_url_with_ms': "http://%s:%d/api/query?start=%s&end=%s&ms=true",
    'metric_suburl': "&m=%s:%s{%s}",
    'metric_suburl_with_rate': "&m=%s:rate:%s{%s}"
  }
}

def filters_to_str(q_filters):
  # We generate a list of key=value pairs in sorted key order. Sorting is not
  # needed by the query, but its just a nice to have to the unit test doesn't
  # trip up due to changing key=value order.
  pair_list = ["%s=%s" % (kk,q_filters[kk]) for kk in sorted(q_filters.keys())]
  return ",".join(pair_list)  # string returned: "key1=value1,key2=value2"
    

'''
  This is a garbage in/garbage out style API. Caller is assumed to have
  validated each parameter before calling.

  The algorithm here is:
   - Construct base URL.
   - Construct metric suburl pieces from the timeseries IDs.
   - Combine base URL and metric suburls into a single fully qualified URL.
'''
def url(tsdb_type, host, tcpport, start_time, end_time, query_aggregator,
        tsid_list, flag_compute_rate=False, flag_ms_response=False):

  # point to TSDB specific templates.
  templates = tsdb_queryurl_templates[tsdb_type]

  # Select the base URL template. We use different template based on whether
  # millisecond response is requested by the caller (or not).
  if flag_ms_response:
      url_template = templates['base_url_with_ms']
  else:
      url_template = templates['base_url']
  base_url = url_template % (host, tcpport, start_time.value, end_time.value)

  # For brevity, suburl = surl

  # Construct metric surl pieces -- To do that first select template and
  # then fill pieces.

  # Based on whether 'rate' is being requested select the right metric surl
  # template to use.
  metric_surl_template = None
  if flag_compute_rate == True:
    metric_surl_template = templates['metric_suburl_with_rate']
  else:
    metric_surl_template = templates['metric_suburl']

  # Each timeseries ID expands into 1 metric_surl_piece. So we walk through
  # all the tsid's and collect all the metric surl pieces in a list.
  metric_surl_pieces = []
  for tsid in tsid_list:
    surl = metric_surl_template % (query_aggregator.name.lower(), \
                                   tsid.metric_id, filters_to_str(tsid.filters))
    metric_surl_pieces.append(surl)
    
  # Combine the base URL and metric surl pieces into one full qualified URL.
  fq_url = "%s%s" % (base_url, "".join(metric_surl_pieces))
                              
  return fq_url  # FIXME: Log the URL before returning.
