# Get Information related to the Heart Rate from the Garmin API using the JSON file extracted
# Requires to have extracted the information from the Garmin API using the script in the url: https://github.com/labcif/Garmin-Connect-API-Extractor
# Author: Fabian Nunes {fabiannunes12@gmail.com}
# Date: 2023-02-24
# Version: 1.0
# Requirements: Python 3.7 or higher, json
import json

from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv


def _to_safe_inline_json(value):
    return (
        json.dumps(value)
        .replace('<', '\\u003c')
        .replace('>', '\\u003e')
        .replace('&', '\\u0026')
    )


def get_hr_api(files_found, report_folder, seeker, wrap_text):

    logfunc("Processing data for Heart Rate API")
    report = ArtifactHtmlReport('Heart Rate API')
    report.start_artifact_report(report_folder, 'Heart Rate API')
    report.add_script()
    data_headers = ('Date', 'Max Hearth Rate', 'Min Hearth Rate', 'Resting Hearth Rate', 'Average Hearth Rate', 'Graphic')
    data_list = []
    chart_actions = {}
    #file = str(files_found[0])
    for file in files_found:
        file = str(file)
        logfunc("Processing file: " + file)
        #Open JSON file
        with open(file, "r") as f:
            data = json.load(f)

        if len(data) > 0:
            logfunc("Found Garmin Presistent file")
            # Get calendar date
            date = data['AllDayHR']['payload']['calendarDate']
            # Get max hearth rate if none set to 'N/A'
            if data['AllDayHR']['payload']['maxHeartRate'] is not None:
                max_hr = data['AllDayHR']['payload']['maxHeartRate']
            else:
                max_hr = 'N/A'
            # Get min hearth rate
            if data['AllDayHR']['payload']['minHeartRate'] is not None:
                min_hr = data['AllDayHR']['payload']['minHeartRate']
            else:
                min_hr = 'N/A'
            # Get resting hearth rate
            if data['AllDayHR']['payload']['restingHeartRate'] is not None:
                resting_hr = data['AllDayHR']['payload']['restingHeartRate']
            else:
                resting_hr = 'N/A'
            # Get average hearth rate
            if data['AllDayHR']['payload']['lastSevenDaysAvgRestingHeartRate'] is not None:
                average_hr = data['AllDayHR']['payload']['lastSevenDaysAvgRestingHeartRate']
            else:
                average_hr = 'N/A'
            # check if data['AllDayHR']['payload']['heartRateValues'] exists
            if data['AllDayHR']['payload']['heartRateValues'] is not None:
                hr_values = json.dumps(data['AllDayHR']['payload']['heartRateValues'])
                # convert to list
                hr_values = hr_values.replace('[', '').replace(']', '').split(',')
                #logfunc(str(hr_values))
                x_list = []
                y_list = []
                # from hr_values get x and y values
                for i in range(len(hr_values)):
                    if i % 2 == 0:
                        x_list.append(float(hr_values[i]))
                    else:
                        #if value is null set to 0
                        if 'null' in hr_values[i]:
                            y_list.append(0)
                        else:
                            y_list.append(float(hr_values[i]))

                #convert timestamp to hh:mm
                #logfunc(str(x_list))
                #logfunc(str(y_list))
                action_id = f'garmin-hr-chart-action-{len(chart_actions)}'
                chart_actions[action_id] = {'x': x_list, 'y': y_list}
                hr_btn = (
                    f'<a class="btn btn-light btn-sm garmin-hr-chart-view" href="#" id="{action_id}">'
                    'View</a>'
                )
            else:
                hr_btn = 'N/A'
            data_list.append((date, max_hr, min_hr, resting_hr, average_hr, hr_btn))
    report.filter_by_date('GarminHRAPI', 0)
    report.write_artifact_data_table(
        data_headers,
        data_list,
        file,
        table_id='GarminHRAPI',
        html_no_escape=['Graphic'],
    )
    chart_actions_js = _to_safe_inline_json(chart_actions)
    report.script_code += f"""<script>
       (function() {{
           const chartActions = {chart_actions_js};
           document.addEventListener('click', function(event) {{
               const trigger = event.target.closest('a.garmin-hr-chart-view');
               if (!trigger) {{
                   return;
               }}
               event.preventDefault();
               const payload = chartActions[trigger.id];
               if (!payload) {{
                   return;
               }}
               createLineChart(
                   JSON.stringify(payload.y || []),
                   JSON.stringify(payload.x || []),
                   true,
                   'Heart Rate Variation',
                   'Time',
                   'BPM'
               );
           }});
       }})();
       </script>
       """
    report.add_chart()
    report.end_artifact_report()
    tsvname = f'Garmin Log'
    tsv(report_folder, data_headers, data_list, tsvname)


__artifacts__ = {
    "GarminHRAPI": (
        "Garmin-API",
        ('*/garmin.api/heart_rate*'),
        get_hr_api)
}
