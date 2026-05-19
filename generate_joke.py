#!/usr/bin/env python3
"""Fetches a programming joke and generates an animated reveal SVG card."""

import json
import os
import textwrap
from urllib.request import urlopen
from urllib.error import URLError

SVG_PATH = os.path.join(os.path.dirname(__file__), 'joke.svg')

JOKE_API = 'https://official-joke-api.appspot.com/jokes/programming/random'

FALLBACKS = [
    ("Why do programmers prefer dark mode?", "Because light attracts bugs!"),
    ("Why did the programmer quit his job?", "Because he didn't get arrays."),
    ("How many programmers does it take to change a lightbulb?", "None, that's a hardware problem."),
    ("Why do Java developers wear glasses?", "Because they don't C#."),
    ("What do you call a programmer from Finland?", "Nerdic."),
]


def fetch_joke():
    try:
        with urlopen(JOKE_API, timeout=10) as resp:
            data = json.loads(resp.read())
            if isinstance(data, list):
                data = data[0]
            return data['setup'], data['punchline']
    except Exception as exc:
        print(f'Warning: could not fetch joke: {exc}')
        import random
        return random.choice(FALLBACKS)


def xml_escape(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;')
             .replace('>', '&gt;').replace('"', '&quot;'))


def make_tspans(lines, x):
    parts = []
    for i, line in enumerate(lines):
        dy = '0' if i == 0 else '24'
        parts.append(f'<tspan x="{x}" dy="{dy}">{xml_escape(line)}</tspan>')
    return '\n      '.join(parts)


def generate_svg(setup, punchline):
    q_lines = textwrap.wrap('Q: ' + setup, 62)
    a_lines = textwrap.wrap('A: ' + punchline, 62)

    q_h = len(q_lines) * 24
    a_h = len(a_lines) * 24

    q_y       = 58
    spinner_y = q_y + q_h + 48
    think_y   = spinner_y + 38
    a_y       = spinner_y + 58
    total_h   = a_y + a_h + 38

    q_tspans = make_tspans(q_lines, 400)
    a_tspans = make_tspans(a_lines, 400)

    return f'''<svg width="800" height="{total_h}" xmlns="http://www.w3.org/2000/svg">
  <rect width="800" height="{total_h}" fill="#282a36" rx="12"/>

  <!-- Question fades in at start -->
  <g opacity="0">
    <animate attributeName="opacity"
      values="0;1;1;1;1;1"
      keyTimes="0;0.08;0.35;0.62;0.9;1"
      dur="10s" repeatCount="indefinite"/>
    <text x="400" y="{q_y}" text-anchor="middle"
      font-family="'Courier New',Courier,monospace" font-size="15" fill="#BD93F9">
      {q_tspans}
    </text>
  </g>

  <!-- Spinner appears for ~3s (3.5s–6.5s of the 10s cycle) -->
  <g opacity="0">
    <animate attributeName="opacity"
      values="0;0;1;1;0;0"
      keyTimes="0;0.32;0.38;0.62;0.68;1"
      dur="10s" repeatCount="indefinite"/>
    <g transform="translate(400,{spinner_y})">
      <circle r="17" fill="none" stroke="#8BE9FD" stroke-width="3"
        stroke-dasharray="62 42" stroke-linecap="round">
        <animateTransform attributeName="transform" type="rotate"
          values="0;360" dur="0.85s" repeatCount="indefinite"/>
      </circle>
    </g>
    <text x="400" y="{think_y}" text-anchor="middle"
      font-family="'Courier New',Courier,monospace" font-size="12" fill="#6272a4">
      thinking...
    </text>
  </g>

  <!-- Answer fades in after spinner -->
  <g opacity="0">
    <animate attributeName="opacity"
      values="0;0;0;1;1;1"
      keyTimes="0;0.62;0.72;0.78;0.9;1"
      dur="10s" repeatCount="indefinite"/>
    <text x="400" y="{a_y}" text-anchor="middle"
      font-family="'Courier New',Courier,monospace" font-size="15" fill="#50FA7B">
      {a_tspans}
    </text>
  </g>
</svg>'''


def main():
    setup, punchline = fetch_joke()
    print(f'Q: {setup}')
    print(f'A: {punchline}')
    svg = generate_svg(setup, punchline)
    with open(SVG_PATH, 'w', encoding='utf-8') as fh:
        fh.write(svg)
    print('joke.svg written.')


if __name__ == '__main__':
    main()
