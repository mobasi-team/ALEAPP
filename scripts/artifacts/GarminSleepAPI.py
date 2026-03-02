# Get Information related to Garmin Sleep API
# Requires to have extracted the information from the Garmin API using the script in the url: https://github.com/labcif/Garmin-Connect-API-Extractor
# Author: Fabian Nunes {fabiannunes12@gmail.com}
# Date: 2023-02-24
# Version: 1.0
# Requirements: Python 3.7 or higher, json and datetime
import datetime
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


def get_sleep_api(files_found, report_folder, seeker, wrap_text):
    logfunc("Processing data for Garmin Sleep API")
    file = str(files_found[0])
    logfunc("Processing file: " + file)
    #Open JSON file
    with open(file, "r") as f:
        data = json.load(f)

    if len(data) > 0:
        logfunc("Found Garmin Sleep API data")
        report = ArtifactHtmlReport('Sleep API')
        report.start_artifact_report(report_folder, 'Sleep API')
        report.add_script()
        data_headers = ('Date', 'Sleep Time', 'Start Time', 'End Time', 'Deep Sleep', 'Light Sleep', 'REM Sleep', 'Awake Sleep', 'Average SPo2', 'Lowest SPo2', 'Highest SPo2', 'Sleep Graphic', 'SPo2 Graphic')
        data_list = []
        sleep_actions = {}
        spo2_actions = {}
        for i in data:
            # Get calendar date
            date = i['dailySleepDTO']['calendarDate']
            # Get sleep time
            sleep_time = i['dailySleepDTO']['sleepTimeSeconds']
            # Convert sleep time to hours
            if sleep_time is not None:
                sleep_time = datetime.timedelta(seconds=sleep_time)
            else:
                sleep_time = 'N/A'
            # Get start time
            start_time = i['dailySleepDTO']['sleepStartTimestampGMT']
            if start_time is not None:
                # Convert start time to hours
                start_time = datetime.datetime.utcfromtimestamp(start_time/1000).strftime('%H:%M:%S')
            else:
                start_time = 'N/A'
            # Get end time
            end_time = i['dailySleepDTO']['sleepEndTimestampGMT']
            if end_time is not None:
                # Convert end time to hours
                end_time = datetime.datetime.utcfromtimestamp(end_time/1000).strftime('%H:%M:%S')
            else:
                end_time = 'N/A'
            # Get deep sleep time
            deep_sleep = i['dailySleepDTO']['deepSleepSeconds']
            if deep_sleep is not None:
                # Convert deep sleep time to hours
                deep_sleep = datetime.timedelta(seconds=deep_sleep)
            else:
                deep_sleep = 'N/A'
            # Get light sleep time
            light_sleep = i['dailySleepDTO']['lightSleepSeconds']
            if light_sleep is not None:
                # Convert light sleep time to hours
                light_sleep = datetime.timedelta(seconds=light_sleep)
            else:
                light_sleep = 'N/A'
            # Get REM sleep time
            rem_sleep = i['dailySleepDTO']['remSleepSeconds']
            if rem_sleep is not None:
                # Convert REM sleep time to hours
                rem_sleep = datetime.timedelta(seconds=rem_sleep)
            else:
                rem_sleep = 'N/A'
            # Get awake sleep time
            awake_sleep = i['dailySleepDTO']['awakeSleepSeconds']
            if awake_sleep is not None:
                # Convert awake sleep time to hours
                awake_sleep = datetime.timedelta(seconds=awake_sleep)
            else:
                awake_sleep = 'N/A'
            # check if averageSpO2Value is not null and it exists
            if 'averageSpO2Value' in i['dailySleepDTO']:
                average_spo2 = i['dailySleepDTO']['averageSpO2Value']
            else:
                average_spo2 = 'N/A'
            # check if lowestSpO2Value is not null and it exists
            if  'lowestSpO2Value' in i['dailySleepDTO']:
                lowest_spo2 = i['dailySleepDTO']['lowestSpO2Value']
            else:
                lowest_spo2 = 'N/A'
            # check if highestSpO2Value is not null and it exists
            if  'highestSpO2Value' in i['dailySleepDTO']:
                highest_spo2 = i['dailySleepDTO']['highestSpO2Value']
            else:
                highest_spo2 = 'N/A'
            # check if sleepGraphic is not null and it exists
            if i['sleepLevels'] is not None:
                if start_time == 'N/A' or end_time == 'N/A':
                    sleep_btn = 'N/A'
                else:
                    sleep_action_id = f'garmin-sleep-action-{len(sleep_actions)}'
                    sleep_actions[sleep_action_id] = i['sleepLevels']
                    sleep_btn = (
                        f'<a class="btn btn-light btn-sm garmin-sleep-graphic" href="#" id="{sleep_action_id}">'
                        'Sleep Graphic</a>'
                    )
            else:
                sleep_btn = 'N/A'
            # check if i['wellnessEpochSPO2DataDTOList'] exists
            if 'wellnessEpochSPO2DataDTOList' in i:
                spo2_action_id = f'garmin-sleep-spo2-action-{len(spo2_actions)}'
                spo2_actions[spo2_action_id] = i['wellnessEpochSPO2DataDTOList']
                spo2_btn = (
                    f'<a class="btn btn-light btn-sm garmin-sleep-spo2" href="#" id="{spo2_action_id}">'
                    'SPo2 Graphic</a>'
                )
            else:
                spo2_btn = 'N/A'
            data_list.append((date, sleep_time, start_time, end_time, deep_sleep, light_sleep, rem_sleep, awake_sleep, average_spo2, lowest_spo2, highest_spo2, sleep_btn, spo2_btn))
        report.filter_by_date('GarminSleepAPI', 0)
        report.write_artifact_data_table(
            data_headers,
            data_list,
            file,
            table_id='GarminSleepAPI',
            html_no_escape=['Sleep Graphic', 'SPo2 Graphic'],
        )
        sleep_actions_js = _to_safe_inline_json(sleep_actions)
        spo2_actions_js = _to_safe_inline_json(spo2_actions)
        report.script_code += f"""<script>
           (function() {{
               const sleepActions = {sleep_actions_js};
               const spo2Actions = {spo2_actions_js};
               document.addEventListener('click', function(event) {{
                   const sleepTrigger = event.target.closest('a.garmin-sleep-graphic');
                   if (sleepTrigger) {{
                       event.preventDefault();
                       if (typeof sleepActions[sleepTrigger.id] !== 'undefined') {{
                           generateChartSleep(JSON.stringify(sleepActions[sleepTrigger.id]));
                       }}
                       return;
                   }}
                   const spo2Trigger = event.target.closest('a.garmin-sleep-spo2');
                   if (!spo2Trigger) {{
                       return;
                   }}
                   event.preventDefault();
                   if (typeof spo2Actions[spo2Trigger.id] !== 'undefined') {{
                       spo2Chart(JSON.stringify(spo2Actions[spo2Trigger.id]));
                   }}
               }});
           }})();
           </script>
           """
        report.add_chart()
        report.end_artifact_report()
        tsvname = f'Garmin Log'
        tsv(report_folder, data_headers, data_list, tsvname)
    else:
        logfunc("No Garmin Sleep API data found")


__artifacts__ = {
    "GarminSleepAPI": (
        "Garmin-API",
        ('*/garmin.api/sleep*'),
        get_sleep_api)
}
