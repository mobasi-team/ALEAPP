#!/usr/bin/env python3
import argparse
import os
import re


_SKIP_DIR_PARTS = {
    os.path.join('scripts', '_elements', 'MDB-Free_4.13.0'),
}


def _is_vendor_or_generated(path):
    normalized = path.replace('\\', '/')
    if normalized.endswith('scripts/tools/audit_raw_html_sinks.py'):
        return True
    if normalized.endswith('.min.js'):
        return True
    for part in _SKIP_DIR_PARTS:
        if part.replace('\\', '/') in normalized:
            return True
    return False


def _iter_files(paths):
    for raw_path in paths:
        path = os.path.abspath(raw_path)
        if os.path.isfile(path):
            yield path
            continue
        for root, _dirs, files in os.walk(path):
            for filename in files:
                if filename.endswith(('.py', '.js')):
                    yield os.path.join(root, filename)


def _add_finding(findings, path, line_number, sink, message):
    findings.append(
        {
            'path': path,
            'line': line_number,
            'sink': sink,
            'message': message,
        }
    )


def audit_paths(paths):
    findings = []
    for file_path in _iter_files(paths):
        if _is_vendor_or_generated(file_path):
            continue

        try:
            with open(file_path, 'r', encoding='utf8') as f:
                lines = f.readlines()
        except (UnicodeDecodeError, OSError):
            continue

        for line_number, line in enumerate(lines, 1):
            if 'audit-ignore' in line:
                continue

            if file_path.endswith('.py'):
                if line.lstrip().startswith('def write_raw_html('):
                    continue
                if 'write_raw_html(' in line and 'trust_html(' not in line:
                    _add_finding(
                        findings,
                        file_path,
                        line_number,
                        'write_raw_html',
                        'write_raw_html call is not wrapped with trust_html(...)',
                    )
                if re.search(r'html_escape\s*=\s*False', line):
                    _add_finding(
                        findings,
                        file_path,
                        line_number,
                        'html_escape_false',
                        'Use html_no_escape=[...] instead of global html_escape=False',
                    )
                if re.search(r'on(click|change)\s*=', line):
                    _add_finding(
                        findings,
                        file_path,
                        line_number,
                        'inline_event_handler',
                        'Inline event handlers are forbidden; use delegated listeners',
                    )
                continue

            if '.innerHTML' in line and '=' in line:
                rhs = line.split('=', 1)[1].strip().rstrip(';')
                if rhs not in ('""', "''"):
                    _add_finding(
                        findings,
                        file_path,
                        line_number,
                        'innerHTML',
                        'Potential unsafe innerHTML assignment',
                    )

            if re.search(r'\b(?:href|src)\s*=\s*(message|url)\b', line):
                _add_finding(
                    findings,
                    file_path,
                    line_number,
                    'url-attr',
                    'Potential unvalidated href/src assignment from attacker-controlled variable',
                )

    return findings


def main(argv=None):
    parser = argparse.ArgumentParser(description='Audit HTML sink safety in ALEAPP scripts.')
    parser.add_argument('paths', nargs='*', default=['scripts'])
    args = parser.parse_args(argv)

    findings = audit_paths(args.paths)
    if findings:
        for finding in findings:
            print(f"{finding['path']}:{finding['line']} [{finding['sink']}] {finding['message']}")
        print(f'Found {len(findings)} potential sink issues.')
        return 1

    print('No unsafe sinks found.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
