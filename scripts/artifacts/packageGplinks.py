
from urllib.parse import quote


from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv, timeline, open_sqlite_db_readonly

def get_packageGplinks(files_found, report_folder, seeker, wrap_text):
    data_list =[]
    
    for file_found in files_found:
        if 'sbin' not in file_found:
            file_found = str(file_found)
            source_file = file_found.replace(seeker.data_folder, '')
    
    with open(file_found) as data:
        values = data.readlines()
        
    for x in values:
        bundleid = x.split(' ', 1)
        bundle_id = bundleid[0]
        safe_bundle_id = quote(bundle_id, safe='')
        url = (
            f'<a href="https://play.google.com/store/apps/details?id={safe_bundle_id}" target="_blank">'
            f'https://play.google.com/store/apps/details?id={safe_bundle_id}</a>'
        )
        data_list.append((bundleid[0], url))

    usageentries = len(data_list)
    if usageentries > 0:
        report = ArtifactHtmlReport('Google Play Links for Apps')
        report.start_artifact_report(report_folder, 'Google Play Links for Apps')
        report.add_script()
        data_headers = ('Bundle ID', 'Possible Google Play Store Link')
        report.write_artifact_data_table(
            data_headers,
            data_list,
            file_found,
            html_no_escape=['Possible Google Play Store Link'],
        )
        report.end_artifact_report()
        
        tsvname = f'Google Play Links for Apps'
        tsv(report_folder, data_headers, data_list, tsvname, source_file)
        
    else:
        logfunc('No Google Play Links for Apps data available')

__artifacts__ = {
        "packageGplinks": (
                "Installed Apps",
                ('*/system/packages.list'),
                get_packageGplinks)
}
