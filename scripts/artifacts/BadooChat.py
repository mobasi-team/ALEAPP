# Get Information related to the Chats of the user with other users from the Badoo app (com.badoo.mobile)
# Author: Fabian Nunes {fabiannunes12@gmail.com}
# Date: 2023-05-03
# Version: 1.0
# Requirements: Python 3.7 or higher, json
import json

from scripts.artifact_report import ArtifactHtmlReport
from scripts.html_security import escape_attr, sanitize_url
from scripts.ilapfuncs import logfunc, tsv, timeline, open_sqlite_db_readonly


def _build_profile_image_html(user_image_url):
    safe_src = escape_attr(sanitize_url(user_image_url))
    return f'<img src="{safe_src}" width="100" height="100" alt="User image">'


def _build_photo_links_html(user_photos):
    links = []
    for index, photo in enumerate(user_photos, 1):
        safe_url = escape_attr(sanitize_url(photo.get('url', '')))
        links.append(f'<a href="{safe_url}" target="_blank" rel="noopener noreferrer">Photo {index}</a><br>')
    return ''.join(links)


def _build_open_chat_link(encrypted_user_id, user_image_url):
    safe_user_id = escape_attr(encrypted_user_id)
    safe_avatar_url = escape_attr(sanitize_url(user_image_url))
    return (
        f'<a href="#" class="btn btn-primary badoo-open-chat" rel="{safe_user_id}" '
        f'title="{safe_avatar_url}">Open Chat</a>'
    )


def _build_chat_bind_script():
    return """
<script>
$(document).ready(function () {
    $(document).on('click', 'a.badoo-open-chat', function (event) {
        event.preventDefault();
        const sender = $(this).attr('rel');
        const avatarUrl = $(this).attr('title') || '';
        if (sender) {
            createChat(sender, avatarUrl);
        }
    });
});
</script>
"""


def get_badoo_chat(files_found, report_folder, seeker, wrap_text):
    logfunc("Processing data for Badoo Conections")
    files_found = [x for x in files_found if not x.endswith('-journal')]
    file_found = str(files_found[0])
    db = open_sqlite_db_readonly(file_found)


    cursor = db.cursor()
    cursor.execute('''
        Select user_id, gender, user_name, user_image_url, age, user_photos, work, education, encrypted_user_id
        from conversation_info
    ''')

    all_rows = cursor.fetchall()
    usageentries = len(all_rows)
    if usageentries > 0:
        logfunc(f"Found {usageentries} entries in conversation_info")
        report = ArtifactHtmlReport('Chat')
        report.start_artifact_report(report_folder, 'Badoo Chat')
        report.add_script()
        report.script_code += _build_chat_bind_script()
        data_headers = ('ID', 'Gender', 'User Name', 'User Image URL', 'Age', 'User Photos', 'Work', 'Education', 'Encrypted User ID', 'Button')
        data_list = []

        for row in all_rows:
            id = row[0]
            gender = row[1]
            if (gender == 0):
                gender_text = "Male"
            elif (gender == 1):
                gender_text = "Female"
            else:
                gender_text = "Other"
            user_name = row[2]
            user_image_url = row[3]
            user_image = _build_profile_image_html(user_image_url)
            age = row[4]
            user_photos = row[5]
            # convert string to array
            user_photos = json.loads(user_photos)
            photo_urls = _build_photo_links_html(user_photos)

            work = row[6]
            education = row[7]
            encrypted_user_id = row[8]
            cursor.execute(
                '''
                Select sender_id, recipient_id, datetime("created_timestamp"/1000,'unixepoch'), payload, payload_type
                from message
                where sender_id = ? or recipient_id = ?
                ''',
                (encrypted_user_id, encrypted_user_id),
            )
            messages = cursor.fetchall()
            usageentries_m = len(messages)
            if usageentries_m > 0:
                logfunc(f"Found {usageentries_m} entries in message")
                message_list = []
                for message in messages:
                    text = message[3]
                    text = json.loads(text)
                    type = message[4]
                    # Check if text exists
                    if type == 'TEXT':
                        message_text = text['text']
                        typeM = 'text'
                    elif type == 'QUESTION_GAME':
                        message_text = text['text']
                        if 'answer_own' in text:
                            message_text = message_text + ';Own Answer:' + text['answer_own']
                        if 'answer_other' in text:
                            message_text = message_text + ';Other Answer:' + text['answer_other']
                        typeM = 'question'
                    elif type == 'INSTANT_VIDEO' or type == 'AUDIO' or type == 'IMAGE':
                        message_text = text['url']
                        typeM = 'url'

                    message_dic = {
                        'sender': message[0],
                        'message': message_text,
                        'time': message[2],
                        'type': typeM
                    }
                    message_list.append(message_dic)
                chat = {'name': user_name, 'messages': message_list}
                chat = json.dumps(chat)
                report.add_chat_invisble(encrypted_user_id, chat)
                button = _build_open_chat_link(encrypted_user_id, user_image_url)
            else:
                button = '<span class="btn btn-primary disabled" role="button" aria-disabled="true">Open Chat</span>'
            data_list.append((id, gender_text, user_name, user_image, age, photo_urls, work, education, encrypted_user_id, button))
        # Filter by date
        table_id = "BadooChat"
        report.write_artifact_data_table(
            data_headers,
            data_list,
            file_found,
            table_id=table_id,
            html_no_escape=['User Image URL', 'User Photos', 'Button'],
        )
        # Add the map to the report
        report.add_section_heading('Badoo Chat')
        report.add_chat()
        report.end_artifact_report()

        tsvname = f'Badoo - Chat'
        tsv(report_folder, data_headers, data_list, tsvname)

        tlactivity = f'Badoo - Chat'
        timeline(report_folder, tlactivity, data_list, data_headers)

    else:
        logfunc('No Badoo Chat data available')

    db.close()


__artifacts__ = {
    "BadooChat": (
        "Badoo",
        ('*com.badoo.mobile/databases/ChatComDatabase*'),
        get_badoo_chat)
}
