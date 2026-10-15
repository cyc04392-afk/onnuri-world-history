#!/usr/bin/env python3
"""Make the claude.ai Artifact variant of index.html (no outer skeleton; title+style first)."""
import os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
# body content starts after <body>
body = s[s.index('<body>') + len('<body>'):]
body = body.replace('</body></html>', '').rstrip()
# move <title> to the very top (already first in body), add a line about running inside claude.ai
body = body.replace('<title>온누리 세계사</title>', '<title>온누리 세계사</title>\n<!-- 세계사능력검정시험 학습 앱 · claude.ai Artifact 판 (PWA 판은 GitHub Pages) -->', 1)
# the skeleton already pads :root with safe-area insets and resets body margin; keep the inline small reset out
open(os.path.join(ROOT, 'artifact', 'index.html'), 'w', encoding='utf-8').write(body)
print('artifact/index.html', len(body), 'bytes')
