import os
import re
import sys
import tempfile
import unittest
from unittest import mock


REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.artifact_report import ArtifactHtmlReport
from scripts.html_security import trust_html
import scripts.artifacts.gmailEmails as gmailEmails_artifact
import scripts.artifacts.gmailIMAPEmails as gmailIMAPEmails_artifact
import scripts.artifacts.googleMapsGmm as googleMapsGmm_artifact
import scripts.artifacts.googleQuickSearchboxRecent as googleQuickSearchboxRecent_artifact
import scripts.artifacts.likee as likee_artifact
import scripts.artifacts.pikpakCloudlist as pikpakCloudlist_artifact
import scripts.artifacts.walStrings as walStrings_artifact
import scripts.artifacts.wellbeingaccount as wellbeingaccount_artifact
import scripts.ilapfuncs as ilapfuncs
import scripts.report as report_module

OWNED_WAVE2_SLICE_A_FILES = (
    'scripts/artifacts/GarminResponse.py',
    'scripts/artifacts/GarminJson.py',
    'scripts/artifacts/GarminGcmJsonActivities.py',
    'scripts/artifacts/GarminSleepAPI.py',
    'scripts/artifacts/GarminStepsAPI.py',
    'scripts/artifacts/GarminHRAPI.py',
    'scripts/artifacts/GarminSPo2.py',
    'scripts/artifacts/GarminChart.py',
    'scripts/artifacts/NikeAMoments.py',
)
OWNED_WAVE2_SLICE_B_FILES = (
    'scripts/artifacts/BadooChat.py',
    'scripts/artifacts/smsmms.py',
    'scripts/artifacts/chatgpt.py',
    'scripts/artifacts/teams.py',
    'scripts/artifacts/teleguard.py',
    'scripts/artifacts/Life360.py',
)
OWNED_WAVE3_SLICE_D1_FILES = (
    'scripts/artifacts/garmin.py',
    'scripts/artifacts/GarminActAPI.py',
    'scripts/artifacts/GarminDailiesAPI.py',
    'scripts/artifacts/GarminFacebook.py',
    'scripts/artifacts/GarminPolyAPI.py',
    'scripts/artifacts/GarminPolyline.py',
    'scripts/artifacts/GarminSleep.py',
    'scripts/artifacts/GarminStressAPI.py',
    'scripts/artifacts/NikePolyline.py',
    'scripts/artifacts/AdidasActivities.py',
    'scripts/artifacts/AdidasGoals.py',
    'scripts/artifacts/AdidasUser.py',
    'scripts/artifacts/PumaActivities.py',
    'scripts/artifacts/PumaUsers.py',
    'scripts/artifacts/RunkeeperActivities.py',
    'scripts/artifacts/RunkeeperUser.py',
)
OWNED_WAVE3_SLICE_D1_HTML_COLUMNS_FILES = (
    'scripts/artifacts/GarminFacebook.py',
    'scripts/artifacts/GarminPolyAPI.py',
    'scripts/artifacts/GarminPolyline.py',
    'scripts/artifacts/GarminSleep.py',
    'scripts/artifacts/NikePolyline.py',
    'scripts/artifacts/AdidasActivities.py',
    'scripts/artifacts/AdidasUser.py',
    'scripts/artifacts/PumaActivities.py',
    'scripts/artifacts/PumaUsers.py',
    'scripts/artifacts/RunkeeperActivities.py',
    'scripts/artifacts/RunkeeperUser.py',
)
OWNED_WAVE3_SLICE_D2_FILES = (
    'scripts/artifacts/BadooConnections.py',
    'scripts/artifacts/burnerContacts.py',
    'scripts/artifacts/burnerMessages.py',
    'scripts/artifacts/burnerSubscription.py',
    'scripts/artifacts/burnerUser.py',
    'scripts/artifacts/WhatsApp.py',
    'scripts/artifacts/sChats.py',
    'scripts/artifacts/meetme.py',
    'scripts/artifacts/lgRCS.py',
    'scripts/artifacts/ChessComAccount.py',
    'scripts/artifacts/ChessComFriends.py',
    'scripts/artifacts/ChessComGames.py',
    'scripts/artifacts/ChessComMessages.py',
    'scripts/artifacts/wireMessenger.py',
)
OWNED_WAVE3_SLICE_D5_FILES = (
    'scripts/artifacts/kleinanzeigen.de.py',
    'scripts/artifacts/life360DriverBehavior.py',
    'scripts/artifacts/recentactivity.py',
    'scripts/artifacts/FCMQueuedMessagesSkype.py',
)
OWNED_WAVE3_SLICE_D5_HTML_FILES = (
    'scripts/artifacts/kleinanzeigen.de.py',
    'scripts/artifacts/recentactivity.py',
    'scripts/artifacts/FCMQueuedMessagesSkype.py',
)
OWNED_WAVE3_SLICE_D4_FILES = (
    'scripts/artifacts/MMWActivities.py',
    'scripts/artifacts/MMWUsers.py',
    'scripts/artifacts/OneDrive_Metadata.py',
    'scripts/artifacts/calllog.py',
    'scripts/artifacts/packageGplinks.py',
    'scripts/artifacts/sharedProto.py',
    'scripts/artifacts/smyFiles2.py',
    'scripts/artifacts/smyfilescache.py',
    'scripts/artifacts/torThumbs.py',
    'scripts/artifacts/vaulty_files.py',
    'scripts/artifacts/vaulty_info.py',
    'scripts/artifacts/blueskysearches.py',
    'scripts/artifacts/Cello.py',
    'scripts/artifacts/libretorrentFR.py',
)
OWNED_WAVE3_SLICE_D3_FILES = (
    'scripts/artifacts/dmss.py',
    'scripts/artifacts/hikvision.py',
    'scripts/artifacts/gboard.py',
    'scripts/artifacts/googleCalendar.py',
    'scripts/artifacts/googleKeepNotes.py',
    'scripts/artifacts/googleNowPlaying.py',
    'scripts/artifacts/googleQuickSearchbox.py',
    'scripts/artifacts/googleTasks.py',
    'scripts/artifacts/googlemapaudio.py',
    'scripts/artifacts/googlemapaudioTemp.py',
    'scripts/artifacts/notificationHistory.py',
    'scripts/artifacts/vlcthumbsADB.py',
    'scripts/artifacts/vlcThumbs.py',
    'scripts/artifacts/torrentData.py',
    'scripts/artifacts/galleryTrash.py',
    'scripts/artifacts/wifiConfigstore2.py',
    'scripts/artifacts/imagemngCache.py',
)


class TestReportXssSecurity(unittest.TestCase):
    def _build_report(self, tmpdir):
        report = ArtifactHtmlReport('Security Test')
        report.start_artifact_report(tmpdir, 'security_test')
        return report

    def _read_report_file(self, tmpdir):
        with open(os.path.join(tmpdir, 'security_test.temphtml'), 'r', encoding='utf8') as f:
            return f.read()

    def test_write_lead_text_escapes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report = self._build_report(tmpdir)
            payload = '<img src=x onerror=alert(1)>'
            report.write_lead_text(payload)
            report.end_artifact_report()

            data = self._read_report_file(tmpdir)
            self.assertIn('&lt;img src=x onerror=alert(1)&gt;', data)
            self.assertNotIn(payload, data)

    def test_write_artifact_data_table_sanitizes_when_html_escape_false(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report = self._build_report(tmpdir)
            dirty = '<img src="javascript:alert(1)" onerror="evil()"><script>alert(1)</script><b>x</b>'
            report.write_artifact_data_table(
                ('Col',),
                [(dirty,)],
                '/tmp/source',
                write_location=False,
                html_escape=False,
                cols_repeated_at_bottom=False,
            )
            report.end_artifact_report()

            data = self._read_report_file(tmpdir)
            self.assertNotIn('javascript:alert(1)', data)
            self.assertNotIn('onerror=', data)
            self.assertNotIn('<script>alert(1)</script>', data)

    def test_write_artifact_data_table_sanitizes_html_no_escape_columns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report = self._build_report(tmpdir)
            report.write_artifact_data_table(
                ('Name', 'Raw'),
                [('<b>alpha</b>', '<a href="javascript:alert(1)" onclick="x()">go</a>')],
                '/tmp/source',
                write_location=False,
                html_escape=True,
                html_no_escape=['Raw'],
                cols_repeated_at_bottom=False,
            )
            report.end_artifact_report()

            data = self._read_report_file(tmpdir)
            self.assertIn('&lt;b&gt;alpha&lt;/b&gt;', data)
            self.assertNotIn('<b>alpha</b>', data)
            self.assertNotIn('javascript:alert(1)', data)
            self.assertNotIn('onclick="x()"', data)

    def test_write_raw_html_sanitizes_untrusted_and_accepts_trusted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report = self._build_report(tmpdir)
            report.write_raw_html('<img src=x onerror="alert(1)"><b>unsafe</b>')
            report.write_raw_html(trust_html('<b>safe</b>'))
            report.end_artifact_report()

            data = self._read_report_file(tmpdir)
            self.assertNotIn('onerror=', data.lower())
            self.assertIn('<b>unsafe</b>', data)
            self.assertIn('<b>safe</b>', data)

    def test_aleapp_sink_helpers_sanitize_untrusted_input(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report = self._build_report(tmpdir)
            report.add_image_file('javascript:alert(1)', '" alt="x', '<img src=x onerror=1>')
            report.add_map('<iframe src="javascript:alert(1)" onload="x"></iframe><script>alert(1)</script>')
            report.add_json_to_artifact('<img onerror=1>', '<img src="javascript:1" onerror=1>', idJ='x" onclick="1')
            report.add_heat_map('"</script><script>alert(1)</script>')
            report.add_chart_script("x');alert(1)//", 'line', '[]', '[]', 't', 'x', 'y')
            report.add_timeline(
                'tid" onclick="1',
                [{'time': '<img onerror=1>', 'type': 'fa" onclick="x', 'text': '<script>1</script>'}],
            )
            report.add_chat_invisble('cid" onmouseover="x', '<img src=x onerror=1>')
            report.add_chat_window('<img onerror=1>Head', '<script>alert(1)</script><p>Body</p>')
            report.end_artifact_report()

            data = self._read_report_file(tmpdir)
            self.assertNotIn('javascript:alert(1)', data)
            self.assertNotIn('<script>alert(1)</script>', data)
            self.assertNotIn('<img src=x onerror=1>', data)
            self.assertNotIn('onmouseover="x', data)
            self.assertNotIn('</script><script>alert(1)</script>', data)

    def test_ilap_logging_and_device_info_escape_dynamic_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, 'Screen Output.html')
            devinfo_path = os.path.join(tmpdir, 'DeviceInfo.html')
            ilapfuncs.OutputParameters.screen_output_file_path = out_path
            ilapfuncs.OutputParameters.screen_output_file_path_devinfo = devinfo_path

            ilapfuncs.logfunc('<img src=x onerror=1>')
            ilapfuncs.logdevinfo('<svg onload=alert(1)>')
            ilapfuncs.identifiers.clear()
            ilapfuncs.identifiers['<script>Cat</script>'] = {
                '<b>Label</b>': {
                    'value': '<img src=x onerror=1>',
                    'source_file': '" onmouseover="x',
                    'artifact': '<u>artifact</u>',
                }
            }
            ilapfuncs.write_device_info()

            with open(out_path, 'r', encoding='utf8') as f:
                screen_data = f.read()
            with open(devinfo_path, 'r', encoding='utf8') as f:
                dev_data = f.read()

            self.assertNotIn('<img src=x onerror=1>', screen_data)
            self.assertIn('&lt;img src=x onerror=1&gt;', screen_data)
            self.assertNotIn('<svg onload=alert(1)>', dev_data)
            self.assertNotIn('<script>Cat</script>', dev_data)
            self.assertNotIn('" onmouseover="x', dev_data)

    def test_html_media_tag_and_media_to_html_sanitize_attributes(self):
        media_html = ilapfuncs.html_media_tag(
            'javascript:alert(1)',
            'image/png',
            'max-height:300px;background:url(javascript:1)',
            'x" onerror="1',
        )
        self.assertNotIn('javascript:alert(1)', media_html)
        self.assertNotIn('onerror="1', media_html)

        with tempfile.TemporaryDirectory() as tmpdir:
            report_folder = os.path.join(tmpdir, 'Report', '_HTML', 'artifact')
            os.makedirs(report_folder, exist_ok=True)
            malicious_name = 'bad" onerror="1.jpg'
            malicious_path = os.path.join(tmpdir, malicious_name)
            with open(malicious_path, 'wb') as f:
                f.write(b'\x00')

            with mock.patch('scripts.ilapfuncs.guess_mime', return_value='image/png'):
                media_code = ilapfuncs.media_to_html(malicious_name, [malicious_path], report_folder)

            self.assertNotIn('onerror="1', media_code)

    def test_report_index_sanitizes_logs_contributors_and_logo_mimetype(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report_folder = os.path.join(tmpdir, 'ALEAPP_Report')
            script_logs = os.path.join(report_folder, 'Script Logs')
            os.makedirs(script_logs, exist_ok=True)

            dirty_tab = '<script>alert(9)</script><a href="javascript:1">bad</a><b>ok</b>'
            for name in ('DeviceInfo.html', 'Screen Output.html', 'ProcessedFilesLog.html'):
                with open(os.path.join(script_logs, name), 'w', encoding='utf8') as f:
                    f.write(dirty_tab)

            casedata = {
                'Case Number': '123',
                'Agency Logo mimetype': 'text/html" onerror="1',
                'Agency Logo base64': 'AAAA',
            }

            contributors = [
                (
                    'Name',
                    'javascript:alert(1)',
                    'bad" onclick="1',
                    'data:text/html;base64,AAAA',
                )
            ]

            with mock.patch.object(report_module, 'aleapp_contributors', contributors):
                report_module.create_index_html(
                    report_folder,
                    1,
                    '00:00:01',
                    'filesystem',
                    '/evidence',
                    '<a class="nav-link" href="index.html">index</a>',
                    casedata,
                    'profile.txt',
                )

            index_path = os.path.join(report_folder, '_HTML', 'index.html')
            with open(index_path, 'r', encoding='utf8') as f:
                index_data = f.read()

            self.assertNotIn('alert(9)', index_data)
            self.assertNotIn('javascript:1', index_data)
            self.assertNotIn('javascript:alert(1)', index_data)
            self.assertNotIn('bad" onclick="1', index_data)
            self.assertNotIn('data:text/html', index_data)

    def test_slice_c_google_maps_manual_link_builder_sanitizes_url_and_label(self):
        output = googleMapsGmm_artifact._safe_anchor_html(
            'javascript:alert(1)" onclick="evil()"',
            '<img src=x onerror=alert(9)>',
        )
        self.assertIn('href="#"', output)
        self.assertNotIn('javascript:alert(1)', output)
        self.assertNotIn('onclick=', output)
        self.assertIn('&lt;img src=x onerror=alert(9)&gt;', output)

    def test_slice_c_pikpak_manual_link_builder_sanitizes_url_and_label(self):
        output = pikpakCloudlist_artifact._safe_anchor_html(
            'javascript:alert(1)',
            '<svg onload=alert(1)>',
        )
        self.assertIn('href="#"', output)
        self.assertNotIn('javascript:alert(1)', output)
        self.assertIn('&lt;svg onload=alert(1)&gt;', output)

    def test_slice_c_wal_strings_link_builder_sanitizes_filename(self):
        output = walStrings_artifact._safe_anchor_html(
            'artifact.txt" onclick="x',
            '<script>alert(1)</script>',
        )
        self.assertNotIn('onclick="', output)
        self.assertNotIn('<script>alert(1)</script>', output)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', output)

    def test_slice_c_likee_link_builder_sanitizes_filename(self):
        output = likee_artifact._safe_anchor_html(
            'likee.txt" onclick="x',
            '<img src=x onerror=1>',
        )
        self.assertNotIn('onclick="', output)
        self.assertNotIn('<img src=x onerror=1>', output)
        self.assertIn('&lt;img src=x onerror=1&gt;', output)

    def test_slice_c_quicksearch_image_html_sanitizes_url_and_title(self):
        output = googleQuickSearchboxRecent_artifact._safe_screenshot_html(
            'folder" onclick="evil()"',
            'shot.jpg" onerror="boom',
        )
        self.assertNotIn('onclick="', output)
        self.assertNotIn('onerror="', output)
        self.assertIn('href="', output)
        self.assertIn('src="', output)

    def test_slice_c_wellbeing_pre_block_escapes_script(self):
        output = wellbeingaccount_artifact._json_pre_block('<script>alert(7)</script>\nline2')
        self.assertIn('&lt;script&gt;alert(7)&lt;/script&gt;', output)
        self.assertIn('<br>', output)
        self.assertNotIn('<script>alert(7)</script>', output)

    def test_slice_c_gmail_email_html_columns_are_pre_sanitized(self):
        dirty = '<a href="javascript:alert(1)" onclick="x()">go</a><script>alert(1)</script><b>ok</b>'
        output = gmailEmails_artifact._sanitize_email_html(dirty)
        self.assertNotIn('javascript:alert(1)', output)
        self.assertNotIn('onclick=', output)
        self.assertNotIn('<script>alert(1)</script>', output)
        self.assertIn('<b>ok</b>', output)

    def test_slice_c_gmail_imap_html_columns_are_pre_sanitized(self):
        dirty = '<img src="javascript:alert(1)" onerror="evil()"><p>ok</p>'
        output = gmailIMAPEmails_artifact._sanitize_email_html(dirty)
        self.assertNotIn('javascript:alert(1)', output)
        self.assertNotIn('onerror=', output)
        self.assertIn('<p>ok</p>', output)

    def test_owned_slice_a_artifacts_avoid_html_escape_false(self):
        for rel_path in OWNED_WAVE2_SLICE_A_FILES:
            file_path = os.path.join(REPO_ROOT, rel_path)
            with self.subTest(path=rel_path):
                with open(file_path, 'r', encoding='utf8') as f:
                    source = f.read()
                self.assertNotIn('html_escape=False', source)

    def test_owned_slice_a_artifacts_avoid_inline_onclick_handlers(self):
        onclick_pattern = re.compile(r'onclick\s*=')
        for rel_path in OWNED_WAVE2_SLICE_A_FILES:
            file_path = os.path.join(REPO_ROOT, rel_path)
            with self.subTest(path=rel_path):
                with open(file_path, 'r', encoding='utf8') as f:
                    source = f.read()
                self.assertIsNone(onclick_pattern.search(source))

    def test_owned_slice_a_artifacts_use_column_scoped_html_rendering(self):
        for rel_path in OWNED_WAVE2_SLICE_A_FILES:
            file_path = os.path.join(REPO_ROOT, rel_path)
            with self.subTest(path=rel_path):
                with open(file_path, 'r', encoding='utf8') as f:
                    source = f.read()
                self.assertIn('html_no_escape', source)

    def test_owned_slice_b_artifacts_avoid_html_escape_false(self):
        for rel_path in OWNED_WAVE2_SLICE_B_FILES:
            file_path = os.path.join(REPO_ROOT, rel_path)
            with self.subTest(path=rel_path):
                with open(file_path, 'r', encoding='utf8') as f:
                    source = f.read()
                self.assertNotIn('html_escape=False', source)

    def test_owned_slice_d2_artifacts_avoid_html_escape_false(self):
        for rel_path in OWNED_WAVE3_SLICE_D2_FILES:
            file_path = os.path.join(REPO_ROOT, rel_path)
            with self.subTest(path=rel_path):
                with open(file_path, 'r', encoding='utf8') as f:
                    source = f.read()
                self.assertNotIn('html_escape=False', source)

    def test_owned_slice_d3_artifacts_avoid_html_escape_false(self):
        html_escape_false_pattern = re.compile(r'html_escape\s*=\s*False')
        for rel_path in OWNED_WAVE3_SLICE_D3_FILES:
            file_path = os.path.join(REPO_ROOT, rel_path)
            with self.subTest(path=rel_path):
                with open(file_path, 'r', encoding='utf8') as f:
                    source = f.read()
                self.assertIsNone(html_escape_false_pattern.search(source))

    def test_slice_b_badoo_helpers_sanitize_chat_urls_and_markup(self):
        import scripts.artifacts.BadooChat as badoo_artifact

        image_html = badoo_artifact._build_profile_image_html('javascript:alert(1)" onerror="x')
        photos_html = badoo_artifact._build_photo_links_html(
            [{'url': 'javascript:alert(2)'}, {'url': 'https://example.com/photo.jpg'}]
        )
        chat_link_html = badoo_artifact._build_open_chat_link('id" onclick="x', 'javascript:alert(3)')

        self.assertIn('src="#"', image_html)
        self.assertNotIn('javascript:alert', image_html)
        self.assertNotIn('onerror="x', image_html)
        self.assertIn('https://example.com/photo.jpg', photos_html)
        self.assertNotIn('href="javascript:alert(2)"', photos_html)
        self.assertIn('class="btn btn-primary badoo-open-chat"', chat_link_html)
        self.assertIn('title="#"', chat_link_html)
        self.assertNotIn('onclick="x"', chat_link_html)

    def test_slice_b_smsmms_media_markup_sanitizes_breakout_and_scheme(self):
        import scripts.artifacts.smsmms as smsmms_artifact

        image_with_breakout = smsmms_artifact._build_mms_media_html('x.jpg" onerror="1', 'safe-folder', 'image/jpeg')
        blocked_scheme = smsmms_artifact._build_mms_media_html('img.jpg', 'javascript:alert(1)', 'image/jpeg')

        self.assertNotIn('onerror="1"', image_with_breakout)
        self.assertIn('src="#"', blocked_scheme)
        self.assertIn('href="#"', blocked_scheme)

    def test_slice_b_teleguard_media_and_avatar_helpers_sanitize(self):
        import scripts.artifacts.teleguard as teleguard_artifact

        media_line = teleguard_artifact._build_media_line_html('<img src="javascript:1">', '<b>x</b><script>1</script>')
        avatar_html = teleguard_artifact._build_avatar_html(b'\x00\x01')

        self.assertNotIn('<script>1</script>', media_line)
        self.assertIn('&lt;b&gt;x&lt;/b&gt;', media_line)
        self.assertNotIn('javascript:1', media_line)
        self.assertIn('src="data:image/jpeg;base64,', avatar_html)

    def test_owned_slice_d1_artifacts_avoid_html_escape_false(self):
        for rel_path in OWNED_WAVE3_SLICE_D1_FILES:
            file_path = os.path.join(REPO_ROOT, rel_path)
            with self.subTest(path=rel_path):
                with open(file_path, 'r', encoding='utf8') as f:
                    source = f.read()
                self.assertNotIn('html_escape=False', source)

    def test_owned_slice_d1_artifacts_avoid_inline_onclick_handlers(self):
        onclick_pattern = re.compile(r'onclick\s*=')
        for rel_path in OWNED_WAVE3_SLICE_D1_FILES:
            file_path = os.path.join(REPO_ROOT, rel_path)
            with self.subTest(path=rel_path):
                with open(file_path, 'r', encoding='utf8') as f:
                    source = f.read()
                self.assertIsNone(onclick_pattern.search(source))

    def test_owned_slice_d1_html_columns_use_column_scoped_rendering(self):
        for rel_path in OWNED_WAVE3_SLICE_D1_HTML_COLUMNS_FILES:
            file_path = os.path.join(REPO_ROOT, rel_path)
            with self.subTest(path=rel_path):
                with open(file_path, 'r', encoding='utf8') as f:
                    source = f.read()
                self.assertIn('html_no_escape', source)

    def test_owned_wave3_slice_d5_artifacts_avoid_html_escape_false(self):
        for rel_path in OWNED_WAVE3_SLICE_D5_FILES:
            file_path = os.path.join(REPO_ROOT, rel_path)
            with self.subTest(path=rel_path):
                with open(file_path, 'r', encoding='utf8') as f:
                    source = f.read()
                self.assertNotIn('html_escape=False', source)

    def test_owned_wave3_slice_d5_html_columns_are_scoped(self):
        for rel_path in OWNED_WAVE3_SLICE_D5_HTML_FILES:
            file_path = os.path.join(REPO_ROOT, rel_path)
            with self.subTest(path=rel_path):
                with open(file_path, 'r', encoding='utf8') as f:
                    source = f.read()
                self.assertIn('html_no_escape', source)

    def test_owned_wave3_slice_d4_artifacts_avoid_html_escape_false(self):
        for rel_path in OWNED_WAVE3_SLICE_D4_FILES:
            file_path = os.path.join(REPO_ROOT, rel_path)
            with self.subTest(path=rel_path):
                with open(file_path, 'r', encoding='utf8') as f:
                    source = f.read()
                self.assertNotIn('html_escape=False', source)

    def test_repo_scripts_avoid_html_escape_false(self):
        pattern = re.compile(r'html_escape\s*=\s*False')
        offenders = []
        scripts_root = os.path.join(REPO_ROOT, 'scripts')
        ignore_rel_paths = {'scripts/tools/audit_raw_html_sinks.py'}

        for root, _dirs, files in os.walk(scripts_root):
            for filename in files:
                if not filename.endswith('.py'):
                    continue
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, REPO_ROOT)
                if rel_path in ignore_rel_paths:
                    continue
                with open(file_path, 'r', encoding='utf8') as f:
                    source = f.read()
                if pattern.search(source):
                    offenders.append(rel_path)

        self.assertEqual([], offenders, msg=f'Files still using html_escape=False: {offenders}')

    def test_repo_artifacts_avoid_inline_onclick_handlers(self):
        onclick_pattern = re.compile(r'onclick\s*=')
        offenders = []
        artifacts_root = os.path.join(REPO_ROOT, 'scripts', 'artifacts')

        for root, _dirs, files in os.walk(artifacts_root):
            for filename in files:
                if not filename.endswith('.py'):
                    continue
                file_path = os.path.join(root, filename)
                with open(file_path, 'r', encoding='utf8') as f:
                    source = f.read()
                if onclick_pattern.search(source):
                    offenders.append(os.path.relpath(file_path, REPO_ROOT))

        self.assertEqual([], offenders, msg=f'Artifacts still using inline onclick: {offenders}')


if __name__ == '__main__':
    unittest.main()
