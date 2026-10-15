#!/usr/bin/env python3
"""Validate a chapter JSON for 온누리 세계사. Usage: validate.py data/chNN.json"""
import json, re, sys

ERR, WARN = [], []
def err(m): ERR.append(m)
def warn(m): WARN.append(m)

path = sys.argv[1]
try:
    d = json.load(open(path, encoding='utf-8'))
except Exception as e:
    print('JSON 파싱 실패:', e); sys.exit(1)

no = d.get('no')
for k in ['no','title','era','summary','flow','q','g','alias','exam','essay','images']:
    if k not in d: err(f'필수 키 없음: {k}')
if 'pages' not in d: d['pages'] = []
ERAS = ['문명의 발생','동아시아','서아시아·인도','유럽·아메리카','제국주의·세계 대전','현대 세계']
if d.get('era') not in ERAS: err(f"era 값이 목록에 없음: {d.get('era')}")

g = d.get('g', {}); alias = d.get('alias', {}); images = d.get('images', {})
gkeys = set(g.keys())
def resolves(t): return t in gkeys or (t in alias and alias[t] in gkeys)

# summary / flow
s = d.get('summary','')
if len(s) < 500: warn(f'summary 짧음 ({len(s)}자, 600~900자 권장)')
fl = d.get('flow', [])
if not (8 <= len(fl) <= 20): warn(f'flow 개수 {len(fl)} (10~16 권장)')
for f in fl:
    if not (isinstance(f, dict) and f.get('t') and f.get('e')): err('flow 항목에 t/e 없음')

# questions
qs = d.get('q', [])
if not (22 <= len(qs) <= 34): warn(f'q 개수 {len(qs)} (26~30 권장)')
seen_n = set(); answers_all = set()
for q in qs:
    n = q.get('n')
    if n in seen_n: err(f'q n 중복: {n}')
    seen_n.add(n)
    t = q.get('text','')
    blanks = re.findall(r'\{\{(.+?)\}\}', t)
    if not blanks: err(f'q{n}: 빈칸 없음')
    if len(blanks) > 3: warn(f'q{n}: 빈칸 {len(blanks)}개 (1~3 권장)')
    outside = re.sub(r'\{\{.+?\}\}', '', t)
    for b in blanks:
        if not re.fullmatch(r'[가-힣]{1,9}', b): err(f'q{n}: 빈칸 "{b}" — 한글 2~7자만 허용(공백·한자·숫자·괄호 금지)')
        elif not (2 <= len(b) <= 7): warn(f'q{n}: 빈칸 "{b}" 길이 {len(b)} (2~7 권장)')
        if b in outside: err(f'q{n}: 정답 "{b}"가 빈칸 밖 문장에 그대로 나옴')
        answers_all.add(b)
    if re.search(r'\{[^{]|[^}]\}', t.replace('{{','').replace('}}','')): err(f'q{n}: 중괄호 형식 오류')
    kw = q.get('kw', [])
    if not (1 <= len(kw) <= 6): warn(f'q{n}: kw {len(kw)}개 (2~5 권장)')
    for k in kw:
        if not resolves(k): err(f'q{n}: kw "{k}"가 사전(g)/alias에 없음')
    if len(q.get('sum','')) < 30: warn(f'q{n}: sum 짧음')
    info = q.get('info', [])
    if not (3 <= len(info) <= 7): warn(f'q{n}: info {len(info)}개 (4~6 권장)')
    for im in q.get('img', []):
        if im not in images: err(f'q{n}: img "{im}" 없음')
    if 'tip' not in q: warn(f'q{n}: tip 없음')
    for b in blanks:
        if not resolves(b) and not any(b in k for k in gkeys): warn(f'q{n}: 빈칸 정답 "{b}"에 해당하는 사전 용어가 없음')

# glossary
if not (40 <= len(g) <= 80): warn(f'g 개수 {len(g)} (50~65 권장)')
CATS = {'개념','인물','사건','왕조/국가','제도','문화/종교','유적/유물','지역','전쟁','조약/문서'}
for k, v in g.items():
    for f in ['cat','def']:
        if not v.get(f): err(f'g[{k}]: {f} 없음')
    if v.get('cat') not in CATS: warn(f'g[{k}]: cat "{v.get("cat")}" 목록 밖')
    if not v.get('bg'): warn(f'g[{k}]: bg 없음')
    body = v.get('body', [])
    if not (1 <= len(body) <= 5): warn(f'g[{k}]: body {len(body)}개')
    if not v.get('sig'): warn(f'g[{k}]: sig 없음')
    if not v.get('fx'): warn(f'g[{k}]: fx 없음')
    for r in v.get('rel', []):
        if r != k and not resolves(r): err(f'g[{k}]: rel "{r}" 사전에 없음')
    for im in v.get('img', []):
        if im not in images: err(f'g[{k}]: img "{im}" 없음')
for a, t in alias.items():
    if t not in gkeys: err(f'alias "{a}" → "{t}" 가 g에 없음')
    if a in gkeys: warn(f'alias "{a}" 가 g의 키이기도 함(불필요)')

# exam
ex = d.get('exam', [])
if not (10 <= len(ex) <= 16): warn(f'exam 개수 {len(ex)} (12~14 권장)')
ids = set()
for e in ex:
    i = e.get('id','')
    if not re.fullmatch(rf'e{no:02d}-\d+', i): err(f'exam id 형식 오류: {i} (e{no:02d}-N)')
    if i in ids: err(f'exam id 중복 {i}')
    ids.add(i)
    opts = e.get('options', [])
    if len(opts) != 5: err(f'{i}: 선지 {len(opts)}개 (5개 필요)')
    if e.get('answer') not in [1,2,3,4,5]: err(f'{i}: answer 1~5 아님')
    if len(e.get('optx', [])) != 5: err(f'{i}: optx 5개 필요')
    if not e.get('expl'): err(f'{i}: expl 없음')
    if not e.get('stem'): err(f'{i}: stem 없음')
    if not e.get('src'): warn(f'{i}: src 없음')
    for k in e.get('kw', []):
        if not resolves(k): err(f'{i}: kw "{k}" 사전에 없음')
    for im in e.get('img', []):
        if im not in images: err(f'{i}: img "{im}" 없음')
    for o in opts:
        if re.match(r'^[①②③④⑤]', o): err(f'{i}: 선지 앞에 ①~⑤ 기호를 쓰지 말 것')

# essay
es = d.get('essay', [])
if not (2 <= len(es) <= 6): warn(f'essay 개수 {len(es)} (3~5 권장)')
for e in es:
    i = e.get('id','')
    if not re.fullmatch(rf's{no:02d}-\d+', i): err(f'essay id 형식 오류: {i}')
    if not e.get('stem'): err(f'{i}: stem 없음')
    pts = e.get('points', [])
    if not (2 <= len(pts) <= 5): warn(f'{i}: points {len(pts)}개 (2~4 권장)')
    if not e.get('model'): err(f'{i}: model 없음')
    for k in e.get('kw', []):
        if not resolves(k): err(f'{i}: kw "{k}" 사전에 없음')

# images
if not (6 <= len(images) <= 24): warn(f'images 개수 {len(images)} (10~18 권장)')
used = set()
for q in qs: used.update(q.get('img', []))
for v in g.values(): used.update(v.get('img', []))
for e in ex: used.update(e.get('img', []))
for k, im in images.items():
    if not re.fullmatch(rf'c{no:02d}_[a-z0-9_]+', k): err(f'image 키 형식 오류: {k} (c{no:02d}_xxx)')
    if im.get('file') != k + '.jpg': err(f'image {k}: file은 "{k}.jpg" 이어야 함')
    if im.get('type') not in ('photo','map','art','doc','gif'): err(f'image {k}: type 오류')
    if not (im.get('commons','').startswith('File:')): err(f'image {k}: commons 파일명은 "File:"로 시작')
    if not im.get('cap'): err(f'image {k}: cap 없음')
    if not im.get('credit'): warn(f'image {k}: credit 없음')
    if not im.get('src'): warn(f'image {k}: src 없음')
    if k not in used: warn(f'image {k}: q/g/exam 어디에서도 참조되지 않음')

print(f'{path}: q {len(qs)} · g {len(g)} · alias {len(alias)} · exam {len(ex)} · essay {len(es)} · images {len(images)} · flow {len(fl)} · summary {len(s)}자')
for m in ERR: print('ERROR:', m)
for m in WARN: print('warn:', m)
print(f'오류 {len(ERR)} · 경고 {len(WARN)}')
sys.exit(1 if ERR else 0)
