# Get JSON information stored in the Garmin GCM database (json_activities table)
# Author: Fabian Nunes {fabiannunes12@gmail.com}
# Date: 2023-02-24
# Version: 1.0
# Requirements: Python 3.7 or higher and json module
import json

from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv, timeline, open_sqlite_db_readonly


def _to_safe_inline_json(value):
    return (
        json.dumps(value)
        .replace('<', '\\u003c')
        .replace('>', '\\u003e')
        .replace('&', '\\u0026')
    )


def get_garmin_gcm_json_activities(files_found, report_folder, seeker, wrap_text):
    logfunc("Processing data for Garmin Response")
    files_found = [x for x in files_found if not x.endswith('wal') and not x.endswith('shm') and not x.endswith('journal')]
    file_found = str(files_found[0])
    db = open_sqlite_db_readonly(file_found)

    cursor = db.cursor()
    cursor.execute('''
    SELECT  
    _id, 
    datetime("saved_timestamp"/1000, 'unixepoch'),
    saved_timestamp,
    concept_id,
    data_type,
    cached_val
    from json_activities
    ''')

    all_rows = cursor.fetchall()
    usageentries = len(all_rows)
    if usageentries > 0:
        logfunc(f"Found {usageentries} Garmin GCM JSON Activities")
        report = ArtifactHtmlReport('JSON Activities')
        report.start_artifact_report(report_folder, 'JSON Activities')
        report.add_script()
        data_headers = ('_id', 'saved_timestamp', 'concept_id', 'data_type', 'json')
        data_list = []
        json_actions = {}

        for index, row in enumerate(all_rows):
            # ignore row that is [] (empty list)
            if row[5] != '[]':
                jsonData = row[5]
                # convert to json
                jsonData = jsonData.replace('\"', '"')
                jsonData = jsonData.replace('"{', '{')
                jsonData = jsonData.replace('}"', '}')
                jsonData = json.loads(jsonData)
                jsonData = json.dumps(jsonData, indent=4, sort_keys=True)
                action_id = f'garmin-gcm-json-action-{index}'
                json_actions[action_id] = jsonData
                data_list.append(
                    (
                        row[0],
                        row[1],
                        row[3],
                        row[4],
                        f'<a class="btn btn-light btn-sm garmin-gcm-json-view" href="#" id="{action_id}">View</a>',
                    )
                )
            else:
                data_list.append((row[0], row[1], row[3], row[4], ''))

        table_id = "garmin_gcm_json_activities"
        report.filter_by_date(table_id, 1)
        report.write_artifact_data_table(
            data_headers,
            data_list,
            file_found,
            table_id=table_id,
            html_no_escape=['json'],
        )

        # Insert pretty JSON into the report
        i = 0
        for row in all_rows:
            # ignore row that is [] (empty list)
            if row[5] != '[]' and i == 0:
                jsonData = row[5]
                #convert to json
                jsonData = jsonData.replace('\"', '"')
                jsonData = jsonData.replace('"{', '{')
                jsonData = jsonData.replace('}"', '}')
                jsonData = json.loads(jsonData)
                jsonData = json.dumps(jsonData, indent=4, sort_keys=True)
                if i == 0:
                    report.add_json_to_artifact("Response", jsonData, False, row[0], True)
                i += 1
        json_actions_js = _to_safe_inline_json(json_actions)
        report.script_code += f"""<script>
           (function() {{
               const actionMap = {json_actions_js};
               document.addEventListener('click', function(event) {{
                   const trigger = event.target.closest('a.garmin-gcm-json-view');
                   if (!trigger) {{
                       return;
                   }}
                   event.preventDefault();
                   const payload = actionMap[trigger.id];
                   if (typeof payload !== 'string') {{
                       return;
                   }}
                   const code = document.getElementById('jsonCode');
                   if (!code) {{
                       return;
                   }}
                   code.textContent = payload;
                   hljs.highlightAll();
               }});
           }})();
           </script>
           """

        report.end_artifact_report()

        tsvname = f'Garmin - Response'
        tsv(report_folder, data_headers, data_list, tsvname)

        tlactivity = f'Garmin - Response'
        timeline(report_folder, tlactivity, data_list, data_headers)

    else:
        logfunc('No Garmin GCM JSON data available')

    db.close()


__artifacts__ = {
    "GarminGcmJsonActivities": (
        "Garmin-GCM",
        ('*/com.garmin.android.apps.connectmobile/databases/gcm_cache.db*'),
        get_garmin_gcm_json_activities)
}
