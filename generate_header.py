#!/usr/bin/env python3
"""Regenerates header.svg with commit-rain columns built from recent GitHub activity."""

import json
import os
from urllib.request import Request, urlopen
from urllib.error import URLError

USERNAME  = 'OzSpidey'
CHAR_H    = 15   # px per character row in a rain column
SVG_PATH  = os.path.join(os.path.dirname(__file__), 'header.svg')

# 14 columns spread across 1200px: (x, fall-duration-seconds, start-offset-seconds)
# Negative offset = column is already mid-fall when the page loads
COLUMNS = [
    ( 40,  5.2, -1.3),
    (120,  4.8, -3.1),
    (200,  6.5, -0.7),
    (285,  5.8, -4.2),
    (370,  7.2, -2.6),
    (455,  4.5, -1.8),
    (540,  6.0, -3.9),
    (625,  5.5, -0.4),
    (710,  7.8, -5.1),
    (795,  5.0, -2.3),
    (875,  6.8, -1.0),
    (955,  4.9, -4.7),
    (1040, 6.2, -3.4),
    (1130, 5.4, -0.9),
]

BEGIN_MARKER = '  <!-- BEGIN COMMIT RAIN -->'
END_MARKER   = '  <!-- END COMMIT RAIN -->'
ANCHOR       = '  <rect width="1200" height="200" fill="url(#bg)"/>'

FALLBACKS = [
    'feat: add pipeline',  'fix: null handler',    'chore: bump deps',
    'refactor: clean util','feat: snowflake query', 'fix: dbt model join',
    'docs: update readme', 'feat: airflow dag',     'fix: api timeout',
    'feat: data quality',  'fix: schema drift',     'chore: lint pass',
    'feat: add monitor',   'fix: edge case',
]


def fetch_commits(token: str, count: int = 14) -> list:
    url = f'https://api.github.com/users/{USERNAME}/events?per_page=100'
    req = Request(url)
    if token:
        req.add_header('Authorization', f'token {token}')
    req.add_header('User-Agent', 'header-generator/1.0')
    try:
        with urlopen(req, timeout=15) as resp:
            events = json.loads(resp.read())
    except URLError as exc:
        print(f'Warning: could not fetch events: {exc}')
        events = []

    messages, seen = [], set()
    skip_phrases = ('[skip ci]', 'update seen jobs', 'update header',
                    'update commit rain', 'merge pull request')
    for ev in events:
        if ev.get('type') != 'PushEvent':
            continue
        for commit in ev.get('payload', {}).get('commits', []):
            msg = commit.get('message', '').split('\n')[0].strip()
            low = msg.lower()
            if msg and msg not in seen and not any(p in low for p in skip_phrases):
                seen.add(msg)
                messages.append(msg[:22])
                if len(messages) >= count:
                    return messages

    for fb in FALLBACKS:
        if len(messages) >= count:
            break
        if fb not in seen:
            messages.append(fb)
    return messages[:count]


def xml_escape(s: str) -> str:
    return (s.replace('&', '&amp;').replace('<', '&lt;')
             .replace('>', '&gt;').replace('"', '&quot;'))


def make_column(x: int, msg: str, dur: float, begin: float) -> str:
    chars = list(msg)
    n = len(chars)
    if not n:
        return ''
    col_h = n * CHAR_H
    lines = ['    <g>',
             f'      <animateTransform attributeName="transform" type="translate"',
             f'        values="0,{-col_h}; 0,220" dur="{dur}s" begin="{begin}s"',
             f'        repeatCount="indefinite" calcMode="linear"/>']
    for i, ch in enumerate(chars):
        y = (i + 1) * CHAR_H
        if i == n - 1:                       # head character: bright white-green
            fill, opacity = '#ccffdd', 0.90
        else:
            progress = (i + 1) / n
            fill    = '#50fa7b'
            opacity = round(0.08 + progress * 0.60, 2)
        lines.append(
            f'      <text x="{x}" y="{y}" fill="{fill}" opacity="{opacity}" '
            f'font-family="\'Courier New\',Courier,monospace" '
            f'font-size="13" font-weight="bold">{xml_escape(ch)}</text>'
        )
    lines.append('    </g>')
    return '\n'.join(lines)


def build_rain_block(messages: list) -> str:
    cols = []
    for i, (x, dur, begin) in enumerate(COLUMNS):
        msg = messages[i] if i < len(messages) else 'git push'
        col = make_column(x, msg, dur, begin)
        if col:
            cols.append(col)
    return (f'{BEGIN_MARKER}\n'
            f'  <g opacity="0.52">\n'
            + '\n'.join(cols) +
            f'\n  </g>\n'
            f'{END_MARKER}')


def update_svg(svg: str, rain_block: str) -> str:
    if BEGIN_MARKER in svg and END_MARKER in svg:
        before = svg[:svg.index(BEGIN_MARKER)]
        after  = svg[svg.index(END_MARKER) + len(END_MARKER):]
        return before + rain_block + after
    # First run: insert right after the background rect
    return svg.replace(ANCHOR, ANCHOR + '\n\n' + rain_block, 1)


def main():
    token    = os.environ.get('GITHUB_TOKEN', '')
    messages = fetch_commits(token)
    print(f'Using {len(messages)} commit messages:')
    for m in messages:
        print(f'  · {m}')

    with open(SVG_PATH, 'r', encoding='utf-8') as fh:
        svg = fh.read()

    updated = update_svg(svg, build_rain_block(messages))

    with open(SVG_PATH, 'w', encoding='utf-8') as fh:
        fh.write(updated)
    print('header.svg updated.')


if __name__ == '__main__':
    main()
