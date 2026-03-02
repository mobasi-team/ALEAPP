import json
import os

from scripts.artifact_report import ArtifactHtmlReport
from scripts.html_security import escape_text
from scripts.ilapfuncs import logfunc, tsv, is_platform_windows 
from scripts.parse3 import ParseProto


def _json_pre_block(value):
    safe_value = escape_text(value).replace('\n', '<br>')
    return f'<pre id="json">{safe_value}</pre>'


def get_wellbeingaccount(files_found, report_folder, seeker, wrap_text):
    file_found = str(files_found[0])
    content = ParseProto(file_found)
    
    content_json_dump = json.dumps(content, indent=4, sort_keys=True, ensure_ascii=False)
    
    report = ArtifactHtmlReport('Wellbeing Account')
    report.start_artifact_report(report_folder, 'Account Data')
    report.add_script()
    data_headers = ('Protobuf Parsed Data', 'Protobuf Data')
    data_list = []
    data_list.append((_json_pre_block(content_json_dump), str(content)))
    report.write_artifact_data_table(
        data_headers,
        data_list,
        file_found,
        html_no_escape=['Protobuf Parsed Data'],
    )
    report.end_artifact_report()
    
    tsvname = f'wellbeing account'
    tsv(report_folder, data_headers, data_list, tsvname)

__artifacts__ = {
        "wellbeingaccount": (
                "Digital Wellbeing",
                ('*/com.google.android.apps.wellbeing/files/AccountData.pb'),
                get_wellbeingaccount)
}
