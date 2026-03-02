# Get Information from the table activity_charts and activitie_details in the database cache-database from Garmin Connect
# Author: Fabian Nunes {fabiannunes12@gmail.com}
# Date: 2023-02-24
# Version: 1.0
# Requirements: Python 3.7 or higher

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


def get_garmin_chart(files_found, report_folder, seeker, wrap_text):
    logfunc("Processing data for Garmin Chart")
    #ignore wal and shm files
    #if machines is macos
    files_found = [x for x in files_found if not x.endswith('wal') and not x.endswith('shm')]
    file_found = str(files_found[0])
    db = open_sqlite_db_readonly(file_found)

    # This query is selecting specific columns from the "activity_details" table and joining it with the
    # "activity_chart_data" table on the "activityId" column. The query is selecting the "activityId", "lastUpdated" in
    # unixepoch format and converted to datetime, "activityName", "startTimeGMT", "activityTypeKey", "distance" rounded to 0 decimal,
    # "duration" divided by 60 and rounded to 0 decimal, "steps", "lastUpdated" in unixepoch format and converted to datetime, "chartType",
    # "chartXList" and "chartYList" from the "activity_chart_data" table. The query is using a LEFT JOIN to join the two tables, meaning that it
    # will return all records from the "activity_details" table, and any matching records from the "activity_chart_data" table. The query also has a
    # WHERE clause that is matching the "activityId" column in both tables, meaning that it will only return rows where the "activityId" in the "activity_details"
    # table matches the "activityId" in the "activity_chart_data" table.

    cursor = db.cursor()
    cursor.execute('''
        Select 
        activity_details.activityId, 
        datetime( activity_details.lastUpdated/1000,'unixepoch'), 
        activityName, 
        startTimeGMT, 
        activityTypeKey, 
        round(distance, 0), 
        round(duration/60, 0), 
        steps, 
        datetime(acd.lastUpdated/1000,'unixepoch'), 
        chartType, 
        chartXList, 
        chartYList
        from activity_details
        left join activity_chart_data acd on activity_details.activityId = acd.activityId
        where activity_details.activityId = acd.activityId
    ''')

    all_rows = cursor.fetchall()
    usageentries = len(all_rows)
    if usageentries > 0:
        logfunc(f'Found {usageentries} activity details')
        report = ArtifactHtmlReport('Charts')
        report.start_artifact_report(report_folder, 'Charts')
        report.add_script()
        data_headers = ('Activity ID', 'Start Time GMT', 'Activity Last Updated', 'Activity Name', 'Activity Type Key', 'Distance', 'Duration', 'Steps', 'Chart Last Updated', 'Chart Type', 'Change Image')
        data_list = []
        imgs = []
        i = 0
        chart_actions = {}

        for row in all_rows:
            # convert string to list
            x = row[10]
            x_list = x[1:-1].split(',')
            y = row[11]
            y_list = y[1:-1].split(',')
            # convert string to float
            x_list = [float(i) for i in x_list]
            y_list = [float(i) for i in y_list]
            # Convert x_list seconds to minutes
            x_list = [round(i / 60, 2) for i in x_list]

            #changeImage is a JS function that will open the image in the html report
            action_id = f'garmin-chart-action-{len(chart_actions)}'
            chart_actions[action_id] = {'x': x_list, 'y': y_list}
            data_list.append(
                (
                    row[0],
                    row[3],
                    row[1],
                    row[2],
                    row[4],
                    row[5],
                    row[6],
                    row[7],
                    row[8],
                    row[9],
                    f'<a class="btn btn-light btn-sm garmin-chart-view" href="#" id="{action_id}">View</a>',
                )
            )
            i += 1

        # Add graph to the report

        # Added feature to allow the user to sort the data by the selected collumns and with the ID of the table
        table_id = "garmin_chart"
        report.filter_by_date(table_id, 1)

        report.write_artifact_data_table(
            data_headers,
            data_list,
            file_found,
            table_id=table_id,
            html_no_escape=['Change Image'],
        )
        chart_actions_js = _to_safe_inline_json(chart_actions)
        report.script_code += f"""<script>
           (function() {{
               const chartActions = {chart_actions_js};
               document.addEventListener('click', function(event) {{
                   const trigger = event.target.closest('a.garmin-chart-view');
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
                       false,
                       'Heart Rate Variation',
                       'Duration',
                       'BPM'
                   );
               }});
           }})();
           </script>
           """
        # Added feature for displaying the image in the html report
        report.add_chart()
        report.end_artifact_report()

        tsvname = f'Garmin - Charts'
        tsv(report_folder, data_headers, data_list, tsvname)

        tlactivity = f'Garmin - Charts'
        timeline(report_folder, tlactivity, data_list, data_headers)

    else:
        logfunc('No Garmin Charts data available')

    db.close()


__artifacts__ = {
    "GarminCharts": (
        "Garmin-Cache",
        ('*/com.garmin.android.apps.connectmobile/databases/cache-database*'),
        get_garmin_chart)
}
