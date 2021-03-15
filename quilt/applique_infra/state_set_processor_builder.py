'''
   class StateSetProcessorBuilder

   This class builds a StateSetProcessor object from the supplied JSON
   description of a state set and returns the object.

   See $HOME/data_platform/design_docs/README.quilt_and_applique_infra_design
   for details.

   Example usage of this class showing simple* usage:
   -------------------------------------------------
   *FIXME: Parag to update this example by 3/16 showing StateSetProcessorBuilder
           can be embedded inside a server for running multiple
           StateSetProcessor objects concurrently.


     ss_builder = StateSetProcessorBuilder()

     new_ss_request_json = blocking_wait_for_new_request()  # see FIXME below

     # Ensure that JSON msg is a valid StateSet request.
     validation_status = ss_builder.validate_request(new_ss_request_json)
     if validation_status != OK:
         return validation_status

     # Build the StateSetProcessor object
     ss_processor = ss_builder.build(new_ss_request_json)

     # As the name suggests, this will block forever.
     # After my FIXME is addressed, ss_processor will have an async_start()
     # which will be non-blocking and is to be used with webserver.
     ss_processor.blocking_start()

'''

import json
import jsonschema

state_set_json_schema_defn = {
}

class StateSetProcessorBuilder(object):
    def __init__(self):
        # This class is stateless. We just maintain a count of the number of
        # times build was called. The constructor is also a good placeholder
        # for storing any common parameters that are needed for all
        # StateSetProcessor
        self.__count = 0

    def validate_request(self, state_set_request):
        return jsonschema.validate(state_set_request,
                                   state_set_json_schema_defn)

    '''
        To understand the format of new_state_set_request, please see
        sample_state_set_provisioning_request.json
    '''
    def build(self, new_state_set_request, tsdb_url):
        if not self.validate_request(new_state_set_request,
                                     state_set_json_schema_defn):
            raise Exception("Invalid request")

        '''
        1. Construct ts_ids (to be queried):
           Iterate over timeseries JSON tags to construct timeseries id object.
        2. Construct temporal state objects:
           Iterate over state definitions to construct:
             2a) output ts_id object (for each state)
             2b) a list of TemporalState objects using 2a & #1
        3. Use #2 to construct the StateSetProcessor object
        '''
        return StateSetProcessor(temporal_state_obj_list, tsdb_url)
