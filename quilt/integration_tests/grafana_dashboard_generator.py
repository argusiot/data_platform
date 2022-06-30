from grafanalib.core import (
    Dashboard, TimeSeries, PieChartv2
)
from grafanalib.opentsdb import OpenTSDBTarget
import json

from numpy import DataSource

from grafanalib._gen import print_dashboard



class AppliqueDashboard:
    def __init__(self, applique_file) -> None:
        with open(applique_file) as app_file:
            self.appliqueJSON = json.load(app_file)
        self.input_ts_list = self.appliqueJSON['input_timeseries']
        self.output_ts = self.appliqueJSON['output_timeseries_template']
        self.state_set = [state_def['label'] for state_def in self.appliqueJSON['state_definitions']]

    def __createDashboard(self):
        panel_list = []
        for ts in self.input_ts_list:
            panel_list.append(self.__createTimeSeries(ts['ts_name'], ts['ts_defn']['metric'], ts['ts_defn']['tags']))
        
        panel_list.append(self.__createPieChart(self.appliqueJSON["name"]))

        dashboard = Dashboard(
            title=self.appliqueJSON["name"],
            panels=panel_list
        ).auto_panel_ids()
        return dashboard

    def __createTimeSeries(self, name, metric, tags):
        return TimeSeries(title=name, dataSource="default", targets=[OpenTSDBTarget(metric=metric, filters=tags)])
    
    def __createPieChart(self, name):
        filter_tags = self.output_ts['tags']
        filtersets = []
        for state in self.state_set:
            state_filter = filter_tags
            state_filter["state"] = state
            filtersets.append(state_filter)
        
        targets = [OpenTSDBTarget(metric=self.output_ts["metric"], filters = st_filter) for st_filter in filtersets]
        return PieChartv2(title=name, dataSource="default", targets=targets)
    
    def writeDashboard(self):
        dashboard = self.__createDashboard()
        print_dashboard(dashboard)

