from grafanalib.core import (
    Dashboard, TimeSeries, PieChartv2, GridPos, Time
)
from grafanalib.opentsdb import OpenTSDBTarget, OpenTSDBFilter
import json, requests

from numpy import DataSource

from grafanalib._gen import print_dashboard, DashboardEncoder



class AppliqueDashboard:
    def __init__(self, applique_file) -> None:
        with open(applique_file) as app_file:
            self.appliqueJSON = json.load(app_file)
        self.input_ts_list = self.appliqueJSON['input_timeseries']
        self.output_ts = self.appliqueJSON['output_timeseries_template']
        self.state_set = [state_def['label'] for state_def in self.appliqueJSON['state_definitions']]

    def __createDashboard(self, time):
        panel_list = []
        panel_list.append(self.__createTimeSeries("Input Timeseries"))
        
        panel_list.append(self.__createPieChart(self.appliqueJSON["name"]))

        dashboard = Dashboard(
            title=self.appliqueJSON["name"],
            panels=panel_list,
            time=time
        ).auto_panel_ids()
        return dashboard

    def __createTimeSeries(self, name):
        targets = []
        for ts in self.input_ts_list:
            filters = []
            for k, v in ts["ts_defn"]["tags"].items():
                filters.append(OpenTSDBFilter(value=v, tag=k, type="literal_or"))
            targets.append(OpenTSDBTarget(metric=ts["ts_defn"]["metric"], aggregator=None, filters=filters))
        return TimeSeries(title=name, dataSource="default", targets=targets, gridPos=GridPos(h=12, w=20, x=0, y=0))
    
    def __createPieChart(self, name):
        filter_tags = self.output_ts['tags']
        metric = self.output_ts["metric"]
        targets = []
        for state in self.state_set:
            state_filter = filter_tags
            state_filter["state"] = state
            filtersets.append(state_filter)
        
        return PieChartv2(title=name, dataSource="default", targets=targets, gridPos=GridPos(h=8, w=16, x=0, y=8), reduceOptionsCalcs=["sum"])
    
    def writeDashboard(self, time):
        dashboard = self.__createDashboard(time)
        print_dashboard(dashboard)

    def get_dashboard_json(self, dashboard, overwrite=False, message="Updated by grafanlib"):
        '''
        get_dashboard_json generates JSON from grafanalib Dashboard object

        :param dashboard - Dashboard() created via grafanalib
        '''

        # grafanalib generates json which need to pack to "dashboard" root element
        return json.dumps(
            {
                "dashboard": dashboard.to_json_data(),
                "overwrite": overwrite,
                "message": message
            }, sort_keys=True, indent=2, cls=DashboardEncoder)


    def upload_to_grafana(self, start, end, server, verify=True, username="admin", password="admin"):
        '''
        upload_to_grafana tries to upload dashboard to grafana and prints response

        :param time - grafanalib time object
        :param server - grafana server name
        :param api_key - grafana api key with read and write privileges
        '''
        dashboard_json = self.get_dashboard_json(self.__createDashboard(Time(start, end)), overwrite=True)

        headers = {'Content-Type': 'application/json'}
        r = requests.post(f"http://{username}:{password}@{server}/api/dashboards/db", data=dashboard_json, headers=headers, verify=verify)
        # TODO: add error handling
        print(f"{r.status_code} - {r.content}")

