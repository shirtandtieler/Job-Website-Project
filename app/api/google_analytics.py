from google.analytics.data_v1beta import BetaAnalyticsDataClient, OrderBy
from google.analytics.data_v1beta.types import Dimension
from google.analytics.data_v1beta.types import Metric
from google.analytics.data_v1beta.types import RunRealtimeReportRequest



def run_realtime_report():
    """Runs a realtime report on a Google Analytics 4 property."""
    property_id = "274997505"
    client = BetaAnalyticsDataClient()

    request = RunRealtimeReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="unifiedScreenName")],
        metrics=[Metric(name="screenPageViews"), Metric(name="activeUsers"), Metric(name="eventCount")],
    )
    response = client.run_realtime_report(request)
    print(response)

# dimension_headers {
#     name: "unifiedScreenName"
# }
# metric_headers {
#     name: "screenPageViews"
#     type_: TYPE_INTEGER
# }
# metric_headers {
#     name: "activeUsers"
#     type_: TYPE_INTEGER
# }
# metric_headers {
#     name: "eventCount"
#     type_: TYPE_INTEGER
# }
# rows {
#     dimension_values {
#     value: "Admin Dashboard"
# }
# metric_values {
#     value: "3"
# }
# metric_values {
#     value: "1"
# }
# metric_values {
#     value: "9"
# }
# }
# row_count: 1
# kind: "analyticsData#runRealtimeReport"
