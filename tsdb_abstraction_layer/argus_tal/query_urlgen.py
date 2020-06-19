'''
  query_urlgen.py

  Generates URLs for queries given all the query paramaters and TSDB type.

  This is a simple stateless module containing only functions to transform
  input to output.
'''

tsdb_to_url_template = {
  
}

def filters_to_str(self, query_filters_dict):
  pair_list = ["%s=%s" % (kk,vv) for kk,vv in self.__query_filters.items()]
  return ",".join(pair_list)  # string returned: "key1=value1,key2=value2"
    

def url():

