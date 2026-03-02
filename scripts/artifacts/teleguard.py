import sqlite3
import json
import base64
from scripts.artifact_report import ArtifactHtmlReport
from scripts.html_security import escape_attr, escape_text, sanitize_html_fragment, sanitize_url
from scripts.ilapfuncs import logfunc, tsv, timeline, open_sqlite_db_readonly, media_to_html


def _build_media_line_html(media_html, label):
    safe_media_html = sanitize_html_fragment(media_html if media_html is not None else '')
    safe_label = escape_text(label if label is not None else '')
    return f'{safe_media_html}<br>{safe_label}<br>'


def _build_avatar_html(avatar_bytes):
    encoded_avatar = base64.b64encode(avatar_bytes).decode("utf-8")
    safe_data_url = escape_attr(sanitize_url(f'data:image/jpeg;base64,{encoded_avatar}', allow_data_media=True))
    return f'<img src="{safe_data_url}" alt="image" width="300">'


def get_teleguard(files_found, report_folder, seeker, wrap_text):
    
    for file_found in files_found:
        if file_found.endswith('teleguard_database.db'):
            db = open_sqlite_db_readonly(file_found)
            cursor = db.cursor()
            cursor.execute('''
                SELECT
                datetime(createDate/1000, 'unixepoch'),
                datetime(userTime/1000, 'unixepoch'),
                type,
                sender,
                receiver,
                content,
                metadata,
                status,
                isEdited
                from messages
            ''')

            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
            if usageentries > 0:
                report = ArtifactHtmlReport('Teleguard Messages')
                report.start_artifact_report(report_folder, 'Teleguard Messages')
                report.add_script()
                data_headers = ('Timestamp', 'User Time', 'Type', 'Sender','Receiver','Content','Media','Status','Is Edited?')
                data_list = []
                for row in all_rows:
                    if row[2] == 'MEDIA':
                        try:
                            mediainfo = json.loads(row[6]) if row[6] else {}
                        except (TypeError, ValueError, json.JSONDecodeError):
                            mediainfo = {}
                        mediafiles = mediainfo.get('files', {}) if isinstance(mediainfo, dict) else {}
                        if isinstance(mediafiles, dict):
                            thumb_parts = []
                            for key, values in mediafiles.items():
                                thumb_parts.append(
                                    _build_media_line_html(
                                        media_to_html(key, files_found, report_folder),
                                        values,
                                    )
                                )
                            thumb = ''.join(thumb_parts)
                        else:
                            thumb = ''
                    else:
                        thumb = row[6]
                            
                    
                    
                    data_list.append((row[0], row[1], row[2], row[3], row[4], row[5], thumb, row[7], row[8]))
        
                report.write_artifact_data_table(
                    data_headers,
                    data_list,
                    file_found,
                    html_no_escape=['Media'],
                )
                report.end_artifact_report()
                
                tsvname = f'Teleguard Messages'
                tsv(report_folder, data_headers, data_list, tsvname)
                
                tlactivity = 'Teleguard Messages'
                timeline(report_folder, tlactivity, data_list, data_headers)
            else:
                logfunc('No Teleguard Messages data available')
        
            db = open_sqlite_db_readonly(file_found)
            cursor = db.cursor()
            cursor.execute('''
                SELECT
                datetime(createDate/1000, 'unixepoch'),
                channelId,
                header,
                content,
                type,
                localStatus,
                viewsCount,
                likesCount,
                dislikesCount,
                metadata,
                media
                from posts
            ''')
            
            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
            if usageentries > 0:
                data_list = []
                for row in all_rows:
                    data_list.append((row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10]))
                    
                report = ArtifactHtmlReport('Teleguard Posts')
                report.start_artifact_report(report_folder, 'Teleguard Posts')
                report.add_script()
                data_headers = ('Timestamp', 'Channel ID', 'Header', 'Content','Type','Local Status','Views Count','Likes Count','Dislikes Count', 'Metadata', 'Media')
                
                report.write_artifact_data_table(data_headers, data_list, file_found)
                report.end_artifact_report()
                
                tsvname = f'Teleguard Posts'
                tsv(report_folder, data_headers, data_list, tsvname)
                
                tlactivity = 'Teleguard Posts'
                timeline(report_folder, tlactivity, data_list, data_headers)
            else:
                logfunc('No Teleguard Posts available')
                
            db = open_sqlite_db_readonly(file_found)
            cursor = db.cursor()
            cursor.execute('''
                SELECT
                datetime(lastActivityTime/1000, 'unixepoch'),
                serverId,
                alias,
                type,
                color,
                avatar,
                options,
                info,
                datetime(lastVisitTime/1000, 'unixepoch'),
                personalId
                from contacts
            ''')
            
            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
            if usageentries > 0:
                data_list = []
                for row in all_rows:
                    if row[5] is not None:
                        avatar = _build_avatar_html(row[5])
                    else:
                        avatar = row[5]
                        
                    data_list.append((row[0], row[1], row[2], row[3], row[4], avatar, row[6], row[7], row[8], row[9]))
                    
                report = ArtifactHtmlReport('Teleguard Contacts')
                report.start_artifact_report(report_folder, 'Teleguard Contacts')
                report.add_script()
                data_headers = ('Last Activity Timestamp', 'Server ID', 'Alias', 'Type','Color','Avatar','Options','Info','Last Visit Time', 'Personal ID')
                
                report.write_artifact_data_table(
                    data_headers,
                    data_list,
                    file_found,
                    html_no_escape=['Avatar'],
                )
                report.end_artifact_report()
                
                tsvname = f'Teleguard Contacts'
                tsv(report_folder, data_headers, data_list, tsvname)
                
                tlactivity = 'Teleguard Contacts'
                timeline(report_folder, tlactivity, data_list, data_headers)
            else:
                logfunc('No Teleguard Contacts available')
                
            db = open_sqlite_db_readonly(file_found)
            cursor = db.cursor()
            cursor.execute('''
                SELECT *
                from
                channels
            ''')
            
            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
            if usageentries > 0:
                data_list = []
                for row in all_rows:
                    data_list.append((row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11]))
                    
                report = ArtifactHtmlReport('Teleguard Channels')
                report.start_artifact_report(report_folder, 'Teleguard Channels')
                report.add_script()
                data_headers = ('ID', 'Alias', 'Description', 'Category','Color','Avatar ID','Subscribers Count','Admin','Posts Count', 'Is Deleted', 'Language','Type')
                
                report.write_artifact_data_table(data_headers, data_list, file_found)
                report.end_artifact_report()
                
                tsvname = f'Teleguard Channels'
                tsv(report_folder, data_headers, data_list, tsvname)
                
            else:
                logfunc('No Teleguard Channels available')
    db.close()

__artifacts__ = {
        "Teleguard": (
                "Teleguard",
                ('*/data/ch.swisscows.messenger.teleguardapp/app_flutter/teleguard_database.db*',
                    '*/data/ch.swisscows.messenger.teleguardapp/cache/**'),
                get_teleguard)
}
