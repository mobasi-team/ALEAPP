# Get Information related to the Garmin - Responses stored in the database cache
# Author: Fabian Nunes {fabiannunes12@gmail.com}
# Date: 2023-02-24
# Version: 1.0
# Requirements: Python 3.7 or higher and json
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


def get_garmin_response(files_found, report_folder, seeker, wrap_text):
    logfunc("Processing data for Garmin Response")
    files_found = [x for x in files_found if not x.endswith('wal') and not x.endswith('shm')]
    file_found = str(files_found[0])
    db = open_sqlite_db_readonly(file_found)

    cursor = db.cursor()
    cursor.execute('''
    SELECT  
    requestUrl, 
    response, 
    datetime("lastUpdate"/1000, 'unixepoch'),
    lastUpdate
    from response_cache
    ''')

    all_rows = cursor.fetchall()
    usageentries = len(all_rows)
    if usageentries > 0:
        logfunc(f"Found {usageentries} Garmin Response")
        report = ArtifactHtmlReport('Response')
        report.start_artifact_report(report_folder, 'Response')
        report.add_script()
        data_headers = ('Last Update', 'Request URL', 'Response')
        data_list = []
        response_actions = {}

        for index, row in enumerate(all_rows):
            action_id = f'garmin-response-action-{index}'
            response_actions[action_id] = str(row[3])
            data_list.append(
                (
                    row[2],
                    row[0],
                    f'<a class="btn btn-light btn-sm garmin-response-view" href="#" id="{action_id}">View</a>',
                )
            )

        table_id = 'garmin_response'
        report.filter_by_date(table_id, 0)
        report.write_artifact_data_table(
            data_headers,
            data_list,
            file_found,
            table_id=table_id,
            html_no_escape=['Response'],
        )

        # Insert pretty JSON into the report
        i = 0
        for row in all_rows:
            jsonData = row[1]
            #convert to json
            jsonData = jsonData.replace('\"', '"')
            jsonData = jsonData.replace('"{', '{')
            jsonData = jsonData.replace('}"', '}')
            jsonData = json.loads(jsonData)
            jsonData = json.dumps(jsonData, indent=4, sort_keys=True)
            if i == 0:
                report.add_json_to_artifact("Response", jsonData, False, row[3])
            else:
                report.add_json_to_artifact("Response", jsonData, True, row[3])
            i += 1
        response_actions_js = _to_safe_inline_json(response_actions)
        report.script_code += f"""<script>
           (function() {{
               const actionMap = {response_actions_js};
               document.addEventListener('click', function(event) {{
                   const trigger = event.target.closest('a.garmin-response-view');
                   if (!trigger) {{
                       return;
                   }}
                   event.preventDefault();
                   const target = actionMap[trigger.id];
                   if (typeof target === 'undefined') {{
                       return;
                   }}
                   changeJSON(String(target));
               }});
           }})();
           </script>
           """
        report.add_script('<script>hljs.highlightAll();</script>')
        report.end_artifact_report()

        tsvname = f'Garmin - Response'
        tsv(report_folder, data_headers, data_list, tsvname)

        tlactivity = f'Garmin - Response'
        timeline(report_folder, tlactivity, data_list, data_headers)

    else:
        logfunc('No Garmin Response data available')

    db.close()


__artifacts__ = {
    "GarminResponse": (
        "Garmin-Cache",
        ('*/com.garmin.android.apps.connectmobile/databases/cache-database*'),
        get_garmin_response)
}
