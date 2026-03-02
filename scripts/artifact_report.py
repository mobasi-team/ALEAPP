import html
import json as jsonlib
import os
import sys
from scripts.html_parts import *
from scripts.html_security import (
    DEFAULT_ALLOWED_TAGS,
    TrustedHtml,
    escape_attr,
    escape_text,
    sanitize_html_fragment,
    sanitize_url,
)
from scripts.version_info import aleapp_version


def _normalize_cell_value(value):
    return '' if value in [None, 'N/A'] else str(value)


_TABLE_CELL_STYLE = (
    'max-width: 44rem; '
    'white-space: pre-wrap; '
    'overflow-wrap: anywhere; '
    'word-break: break-word;'
)
_EXPANDED_CONTENT_STYLE = (
    'margin-top: 0.4rem; '
    'max-height: 18rem; '
    'overflow: auto; '
    'white-space: pre-wrap; '
    'overflow-wrap: anywhere; '
    'word-break: break-word;'
)
_SUMMARY_STYLE = (
    'cursor: pointer; '
    'white-space: normal; '
    'overflow-wrap: anywhere; '
    'word-break: break-word;'
)
_CELL_EXPAND_THRESHOLD = 512
_CELL_PREVIEW_CHARS = 240


def _format_text_table_cell(value):
    raw_text = _normalize_cell_value(value)
    safe_full_text = escape_text(raw_text)
    if len(raw_text) <= _CELL_EXPAND_THRESHOLD:
        return f'<td style="{_TABLE_CELL_STYLE}">{safe_full_text}</td>'

    safe_preview = escape_text(raw_text[:_CELL_PREVIEW_CHARS])
    hidden_chars = len(raw_text) - _CELL_PREVIEW_CHARS
    return (
        f'<td style="{_TABLE_CELL_STYLE}">'
        f'<details>'
        f'<summary style="{_SUMMARY_STYLE}">{safe_preview} '
        f'<span class="text-muted">... ({hidden_chars} more chars)</span></summary>'
        f'<div style="{_EXPANDED_CONTENT_STYLE}">{safe_full_text}</div>'
        f'</details>'
        f'</td>'
    )


def _escape_inline_script_literal(literal):
    # Prevent </script> and HTML parser breakouts in inline script blocks.
    return (
        literal.replace('<', '\\u003c')
        .replace('>', '\\u003e')
        .replace('&', '\\u0026')
        .replace('\u2028', '\\u2028')
        .replace('\u2029', '\\u2029')
    )


def _to_js_literal(value):
    if isinstance(value, (dict, list, int, float, bool)) or value is None:
        return _escape_inline_script_literal(jsonlib.dumps(value))
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return '""'
        try:
            parsed = jsonlib.loads(stripped)
            return _escape_inline_script_literal(jsonlib.dumps(parsed))
        except (TypeError, ValueError):
            return _escape_inline_script_literal(jsonlib.dumps(value))
    return _escape_inline_script_literal(jsonlib.dumps(str(value)))


_MAP_ALLOWED_TAGS = set(DEFAULT_ALLOWED_TAGS) | {'iframe'}

class ArtifactHtmlReport:

    def __init__(self, artifact_name, artifact_category=''):
        self.report_file = None
        self.report_file_path = ''
        self.script_code = ''
        self.artifact_name = artifact_name
        self.artifact_category = artifact_category # unused

    def __del__(self):
        if self.report_file:
            self.end_artifact_report()

    def start_artifact_report(self, report_folder, artifact_file_name, artifact_description=''):
        '''Creates the report HTML file and writes the artifact name as a heading'''
        self.report_file = open(os.path.join(report_folder, f'{artifact_file_name}.temphtml'), 'w', encoding='utf8')
        self.report_file.write(page_header.format(f'ALEAPP - {self.artifact_name} report'))
        self.report_file.write(body_start.format(f'ALEAPP {aleapp_version}'))
        self.report_file.write(body_sidebar_setup)
        self.report_file.write(body_sidebar_dynamic_data_placeholder) # placeholder for sidebar data
        self.report_file.write(body_sidebar_trailer)
        self.report_file.write(body_main_header)
        self.report_file.write(body_main_data_title.format(f'{self.artifact_name} report', artifact_description))
        self.report_file.write(body_spinner) # Spinner till data finishes loading

    def add_script(self, script=''):
        '''Adds a default script or the script supplied'''
        if script:
            self.script_code += script + nav_bar_script_footer
        else:
            self.script_code += default_responsive_table_script + nav_bar_script_footer

    def write_artifact_data_table(
        self,
        data_headers,
        data_list,
        source_path,
        write_total=True,
        write_location=True,
        html_escape=True,
        cols_repeated_at_bottom=True,
        table_responsive=True,
        table_style='',
        table_id='dtBasicExample',
        html_no_escape=[]
    ):
        ''' Writes info about data, then writes the table to html file
            Parameters
            ----------
            data_headers   : List/Tuple of table column names

            data_list      : List/Tuple of lists/tuples which contain rows of data

            source_path    : Source path of data

            write_total    : Toggles whether to write out a line of total rows written

            write_location : Toggles whether to write the location of data source

            html_escape    : If True (default), then html special characters are encoded

            cols_repeated_at_bottom : If True (default), then col names are also at the bottom of the table

            table_responsive : If True (default), div class is table_responsive

            table_style    : Specify table style like "width: 100%;"

            table_id       : Specify an identifier string, which will be referenced in javascript

            html_no_escape  : if html_escape=True, list of columns not to escape
        '''
        if (not self.report_file):
            raise ValueError('Output report file is closed/unavailable!')

        num_entries = len(data_list)
        if write_total:
            self.write_minor_header(f'Total number of entries: {num_entries}', 'h6')
        if write_location:
            if sys.platform == 'win32':
                source_path = source_path.replace('/', '\\')
            if source_path.startswith('\\\\?\\'):
                source_path = source_path[4:]
            self.write_lead_text(f'{self.artifact_name} located at: {source_path}')

        self.report_file.write('<br />')

        if table_responsive:
            self.report_file.write("<div class='table-responsive'>")

        table_head = '<table id="{}" class="table table-striped table-bordered table-xsm" cellspacing="0" {}>' \
                     '<thead>'.format(table_id, (f'style="{table_style}"') if table_style else '')
        self.report_file.write(table_head)
        self.report_file.write(
            '<tr>' + ''.join(('<th class="th-sm">{}</th>'.format(html.escape(str(x))) for x in data_headers)) + '</tr>')
        self.report_file.write('</thead><tbody>')

        if html_escape:
            for row in data_list:
                if html_no_escape:
                    self.report_file.write('<tr>' + ''.join((
                        _format_text_table_cell(x)
                        if h not in html_no_escape
                        else '<td>{}</td>'.format(sanitize_html_fragment(_normalize_cell_value(x)))
                        for x, h in zip(row, data_headers)
                    )) + '</tr>')
                else:
                    self.report_file.write('<tr>' + ''.join(
                        (_format_text_table_cell(x) for x in
                         row)) + '</tr>')
        else:
            for row in data_list:
                self.report_file.write('<tr>' + ''.join(
                    ('<td>{}</td>'.format(sanitize_html_fragment(_normalize_cell_value(x))) for x in row)
                ) + '</tr>')
        
        self.report_file.write('</tbody>')
        if cols_repeated_at_bottom:
            self.report_file.write('<tfoot><tr>' + ''.join(
                ('<th>{}</th>'.format(html.escape(str(x))) for x in data_headers)) + '</tr></tfoot>')
        self.report_file.write('</table>')
        if table_responsive:
            self.report_file.write("</div>")

    def add_section_heading(self, heading, size='h2'):
        heading = html.escape(heading)
        data = '<div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">' \
               '    <{0} class="{0}">{1}</{0}>' \
               '</div>'
        self.report_file.write(data.format(size, heading))

    def write_minor_header(self, heading, heading_tag=''):
        heading = html.escape(heading)
        if heading_tag:
            self.report_file.write(f'<{heading_tag}>{heading}</{heading_tag}>')
        else:
            self.report_file.write(f'<h3 class="h3">{heading}</h3>')

    def write_lead_text(self, text):
        self.report_file.write(f'<p class="lead">{escape_text(text)}</p>')

    def write_raw_html(self, code):
        if not isinstance(code, TrustedHtml):
            raise TypeError('write_raw_html only accepts TrustedHtml instances')
        self.report_file.write(str(code))

    def end_artifact_report(self):
        if self.report_file:
            self.report_file.write(body_main_trailer + body_end + self.script_code + page_footer)
            self.report_file.close()
            self.report_file = None

    # Add image to artifact
    def add_image_file(self, param, param1, param2, secondImage=False):
        safe_src = escape_attr(sanitize_url(param, allow_data_media=True))
        safe_alt = escape_attr(param1)
        safe_title_attr = escape_attr(param2)
        safe_title_text = escape_text(param2)
        # break line
        self.report_file.write('<br/><hr>')
        # Heading
        self.report_file.write(f'<h3 class="h3 text-center mb-3">{safe_title_text}</h3>')
        # Image centered
        if secondImage:
            self.report_file.write(
                f'<img src="{safe_src}" alt="{safe_alt}" title="{safe_title_attr}" class="img-fluid mx-auto d-block"/>')
        else:
            self.report_file.write(
                f'<img src="{safe_src}" alt="{safe_alt}" title="{safe_title_attr}" id="chartImage" class="img-fluid mx-auto d-block"/>')

    # Add Map Element to artifact
    def add_map(self, param):
        self.report_file.write(sanitize_html_fragment(param, allowed_tags=_MAP_ALLOWED_TAGS))

    # Add Chart Element to artifact
    def add_chart(self, height=400):
        # break line
        self.report_file.write('<br/><hr>')
        # Heading
        self.report_file.write(f'<h3 class="h3 text-center mb-3">Data Chart</h3>')
        self.report_file.write(f'<div style="height:{height}px;" class="d-flex justify-content-center">')
        # Chart
        self.report_file.write(f'<canvas id="myChart"></canvas>')
        self.report_file.write('</div>')

    # Add JSON Element to artifact
    def add_json_to_artifact(self, param, param1, hidden=True, idJ='', gcm=False):
        safe_id = escape_attr(idJ)
        safe_heading = escape_text(param)
        safe_json = escape_text(param1)
        # Div
        if not gcm:
            if hidden:
                self.report_file.write(f'<div id="{safe_id}" class="jsonBlock" style="display:none">')
            else:
                self.report_file.write(f'<div id="{safe_id}" class="jsonBlock">')
            # break line
            self.report_file.write('<br/><hr>')
            # Heading
            self.report_file.write(f'<h3 class="h3 text-center mb-3">{safe_heading}</h3>')
            # Image centered
            self.report_file.write(f'<pre><code>{safe_json}</code></pre>')
            # Div
            self.report_file.write('</div>')
        else:
            self.report_file.write(f'<div class="jsonBlock">')
            # break line
            self.report_file.write('<br/><hr>')
            # Heading
            self.report_file.write(f'<h3 class="h3 text-center mb-3">{safe_heading}</h3>')
            # Image centered
            self.report_file.write(f'<pre><code id="jsonCode">{safe_json}</code></pre>')
            # Div
            self.report_file.write('</div>')
            self.report_file.write('<script>hljs.highlightAll();</script>')

        # Function to create invisible elment to store data

    # Function to create a filter for the datatable
    def filter_by_date(self, id, col1):
        # Row with 2 columns
        self.report_file.write('<div class="row">')
        # Column 1
        self.report_file.write('<div class="col-md-6">')
        # Date picker 1 with default value
        self.report_file.write('<div class="form-group">')
        self.report_file.write('<label for="dateFrom">From</label>')
        self.report_file.write('<input type="date" class="form-control" id="dateFrom" value="2019-01-01">')
        self.report_file.write('</div>')
        # Column 1
        self.report_file.write('</div>')

        # Column 2
        self.report_file.write('<div class="col-md-6">')
        # Date picker 2 with default value
        self.report_file.write('<div class="form-group">')
        self.report_file.write('<label for="dateTo">To</label>')
        self.report_file.write('<input type="date" class="form-control" id="dateTo">')
        self.report_file.write('</div>')
        # Column 2
        self.report_file.write('</div>')
        # Row
        self.report_file.write('</div>')

        # Add JS to filter data only after jquery is loaded
        self.script_code += f"""<script>
           $(document).ready(function() {{
               var table = $('#{id}').DataTable();
               //Put current date in dateTo
               var today = new Date();
               var dd = today.getDate();
               var mm = today.getMonth()+1; //January is 0!
               var yyyy = today.getFullYear();
               if(dd<10){{
                   dd='0'+dd
               }}
               if(mm<10){{
                   mm='0'+mm
               }}
               today = yyyy+'-'+mm+'-'+dd;
               $('#dateTo').val(today);
               // All data above or equal to dateFrom and below or equal to dateTo
               $.fn.dataTable.ext.search.push(
                   function(settings, data, dataIndex) {{
                       var dateFrom = new Date($('#dateFrom').val());
                       var dateTo = new Date($('#dateTo').val());
                       var date = new Date(data[{col1}]);
                       if (dateFrom <= date && date <= dateTo) {{
                           return true;
                       }}
                       return false;
                   }}
               );
               // Event listener to the two range filtering inputs to redraw on input
               $('#dateFrom, #dateTo').change(function() {{
                   table.draw();
               }});
           }});
           </script>
           """

    # Function to add a heatmap to the artifact
    def add_heat_map(self, json):
        safe_json = _to_js_literal(json)
        # year input
        self.report_file.write('<div class="row">')
        self.report_file.write('<div class="col-md-2">')
        self.report_file.write('<div class="form-group">')
        self.report_file.write('<label for="year">Year</label>')
        self.report_file.write(
            '<input type="number" class="form-control" id="year" value="2022">')
        self.report_file.write('</div>')
        self.report_file.write('</div>')
        self.report_file.write('</div>')
        # break line
        # Heading
        self.report_file.write(f'<h3 class="h3 text-center mb-3">Nº Activities</h3>')
        # Image centered
        self.report_file.write(f'<div id="heatmap" class="overflow-auto d-flex justify-content-center"></div><br>')
        self.report_file.write('<a class="btn btn-sm btn-secondary ml-xs heatmap-previous" href="#">← Previous</a>')
        self.report_file.write('<a class="btn btn-sm btn-secondary ml-xs heatmap-next" href="#">Next →</a>')
        self.report_file.write('<br/><hr>')
        # heatmap function
        self.script_code += f"""<script>
           $(document).ready(function() {{
           heatMap({safe_json});
           }});
           $(document).on('change', '#year', function() {{
               changeYear(this);
           }});
           $(document).on('click', 'a.heatmap-previous', function(event) {{
               event.preventDefault();
               previous();
           }});
           $(document).on('click', 'a.heatmap-next', function(event) {{
               event.preventDefault();
               next();
           }});
           </script>
           """

    # Function to add a chart to the artifact using a script call
    def add_chart_script(self, id, type, data, labels, title, xLabel, yLabel):
        safe_id = _to_js_literal(str(id) if id is not None else '')
        safe_type = _to_js_literal(str(type) if type is not None else '')
        safe_data = _to_js_literal(data)
        safe_labels = _to_js_literal(labels)
        safe_title = _to_js_literal(str(title) if title is not None else '')
        safe_x_label = _to_js_literal(str(xLabel) if xLabel is not None else '')
        safe_y_label = _to_js_literal(str(yLabel) if yLabel is not None else '')
        self.script_code += f"""<script>
           createChart({safe_id}, {safe_type}, {safe_data}, {safe_labels}, {safe_title}, {safe_x_label}, {safe_y_label});
           </script>
           """

    #Fucntion to add a timeline to the artifact
    def add_timeline(self, id, dataDict):
        safe_id = escape_attr(id)
        self.report_file.write(
            f'<div class="timeline" data-vertical-start-position="right" data-vertical-trigger="150px" id="{safe_id}" hidden>'
        )
        self.report_file.write('<div class="timeline__wrap">')
        self.report_file.write('<div class="timeline__items">')
        for data in dataDict:
            safe_time = escape_text(data.get("time", ""))
            safe_type = ''.join(ch for ch in str(data.get("type", "")) if ch.isalnum() or ch in '-_ ')
            safe_text = sanitize_html_fragment(data.get("text", ""))
            self.report_file.write('<div class="timeline__item">')
            self.report_file.write('<div class="timeline__content">')
            self.report_file.write(
                f'<h2>{safe_time} <i class="{escape_attr(safe_type)}" style="padding-left: 10px"></i></h2>')
            self.report_file.write(f'<p>{safe_text}</p>')
            self.report_file.write('</div>')
            self.report_file.write('</div>')
        self.report_file.write('</div>')
        self.report_file.write('</div>')
        self.report_file.write('</div>')

    # Function to add a timeline script to the artifact
    def add_timeline_script(self):
        self.script_code += f"""<script>
            $(document).ready(function() {{
                $('.timeline').timeline();
            }});
            </script>
            """

    # Function to add a chat window to the artifact
    def add_chat(self):
        self.report_file.write('<div class="container py-5">')
        self.report_file.write('<div class="row d-flex justify-content-center">')
        self.report_file.write('<div class="col-md-8 col-lg-6 col-xl-4">')
        self.report_file.write('<div class="card" id="chat">')
        self.report_file.write('<div class="card-header d-flex justify-content-center align-items-center p-3 bg-dark text-white border-bottom-0">')
        self.report_file.write('<p class="mb-0 fw-bold" id="title">Chat</p>')
        self.report_file.write('</div>')
        self.report_file.write('<div class="card-body" id="text-area">')
        self.report_file.write('</div>')
        self.report_file.write('</div>')
        self.report_file.write('</div>')
        self.report_file.write('</div>')
        self.report_file.write('</div>')

    # Function to add a empty element with the data to be added later (roundabout way to add data to the chat)
    def add_chat_invisble(self, id, text):
        self.report_file.write(f'<div id="{escape_attr(id)}" hidden>{escape_text(text)}</div>')

    def add_chat_window(self, head, body):
        safe_head = sanitize_html_fragment(head)
        safe_body = sanitize_html_fragment(body)
        self.report_file.write('<div id="chatmaster">')
        self.report_file.write('<div class="chathead">')
        self.report_file.write(f'{safe_head}')
        self.report_file.write('</div>')
        self.report_file.write(f'{safe_body}')
        self.report_file.write('</div>')
