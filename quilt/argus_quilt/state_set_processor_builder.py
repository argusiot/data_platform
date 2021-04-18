'''
   class StateSetProcessorBuilder

   This class builds a StateSetProcessor object from the supplied JSON
   description of a state set and returns the object.

   See $HOME/data_platform/design_docs/README.quilt_and_applique_infra_design
   for details.

   Example usage of this class showing simple* usage:
   -------------------------------------------------
   *FIXME: Parag to update this example by 3/19 showing StateSetProcessorBuilder
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

from argus_tal.timeseries_id import TimeseriesID
from .temporal_state import TemporalState
from .state_set_processor import StateSetProcessor

import json
import jsonschema

class StateSetProcessorBuilder(object):
    def __init__(self, state_set_json_schema_file_path, tsdb_source_url):
        # From the POV of state set processor construction, this class is
        # stateless.
        self.__build_success_count = 0

        #                         Open question:
        # Should the TSDB source be supplied to the builder in the constructor
        # or should should it come in the JSON request.
        #                          Not clear !!
        self.__tsdb_url = tsdb_source_url

        self.__state_set_json_schema = None
        with open(state_set_json_schema_file_path, 'r') as file:
            self.__state_set_json_schema = json.load(file)

    @property
    def build_success_count(self):
        return self.__build_success_count

    def validate_request(self, state_set_request):
        return jsonschema.validate(state_set_request,
                                   self.__state_set_json_schema)

    '''
    Lets build the StateSetProcessor object from the supplied JSON request.
    We build the object hierarchy bottom-up:
    1. Construct ts_ids (to be queried):
       Iterate over timeseries JSON tags to construct timeseries id object.
    2. Construct temporal state objects:
       Iterate over state definitions to construct:
         2a) output ts_id object (for each state)
         2b) a list of TemporalState objects using 2a & #1
    3. Use #2 to construct the StateSetProcessor object

    To understand the format of new_request, please see
    sample_state_set_provisioning_request.json

    Inputs:
        new_request - A JSON object expected to be compliant with the
                      StateSetSchema.json. The compliance validation has not
                      yet been done.
        state_set_json_schema_defn - A reference to the schema defined in
                      StateSetSchema.json.
    '''
    def build(self, new_request):
        # We still validate before we start the building process.
        self.validate_request(new_request)

        '''
        1. "input_timeseries" processing

        Begin by building TimeseriesID objects for timeseries supplied in
        the "input_timeseries" section.
        '''
        tsid_obj_fixup_map = {}
        for fq_ts in new_request["input_timeseries"]:
            ts_name = fq_ts["ts_name"]
            ts_defn = fq_ts["ts_defn"]
            tsid_obj_fixup_map[ts_name] = TimeseriesID(ts_defn["metric"],
                                                       ts_defn["tags"])

        '''
        2a. "output_timeseries_template" pre-processing

        Pre-process the "output_timeseries_template" so we generate the
        output ts_ids later.
        '''
        output_metric, output_tag_template = \
            (new_request["output_timeseries_template"]["metric"],
             new_request["output_timeseries_template"]["tags"])

        '''
        2b. "state_definitions" processing

        Process "states" to genearte the TemporalState objects.
        '''
        temporal_state_obj_list = []
        for sd in new_request["state_definitions"]:
            state_label = sd["label"]
            assert sd["expression_operator"] == "AND"
            state_expr_list = []
            for idx, stmt in enumerate(sd["expression"]):
                ts_name, stmt_operator, filter_val = stmt
                state_expr_list.append( \
                    (tsid_obj_fixup_map[ts_name], stmt_operator, filter_val))

            # Create the output timeseries id object. Fixup the state label
            # before creating the ts_id object.
            temp_tags = dict(output_tag_template)
            temp_tags["state_label"] = state_label
            out_ts_id_obj = TimeseriesID(output_metric, temp_tags)

            # We have everything needed to initiaize the TemporalState object.
            temporal_state_obj_list.append(TemporalState( \
                state_label, state_expr_list, out_ts_id_obj))

        self.__build_success_count += 1
        return StateSetProcessor(new_request["name"],
                                 temporal_state_obj_list,
                                 self.__tsdb_url)
