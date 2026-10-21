#!/usr/bin/env python3
"""Build data/index.json, data/glossary.json, data/exam_all.json from data/chNN.json files."""
import json, os, re, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, 'data')

# full 34-chapter plan (title, era, stage)
PLAN = [
 (1,'인류의 출현과 선사 문화','문명의 발생',1),(2,'메소포타미아·이집트 문명','문명의 발생',1),(3,'인더스·황허 문명','문명의 발생',1),
 (4,'춘추 전국 시대와 제자백가','동아시아',1),(5,'진·한 제국','동아시아',1),(6,'위진 남북조·수·당','동아시아',1),(7,'동아시아 문화권의 형성','동아시아',1),(8,'송·원','동아시아',1),
 (9,'명·청','동아시아',2),(10,'일본의 무가 정권과 동아시아 교역','동아시아',2),
 (11,'서아시아의 고대 제국','서아시아·인도',2),(12,'이슬람 세계의 성립','서아시아·인도',2),(13,'이슬람 세계의 확장','서아시아·인도',2),(14,'고대 인도','서아시아·인도',2),(15,'인도의 이슬람 왕조와 동남아시아','서아시아·인도',2),
 (16,'그리스 세계','유럽·아메리카',2),
 (17,'헬레니즘과 로마 공화정','유럽·아메리카',3),(18,'로마 제국과 크리스트교','유럽·아메리카',3),(19,'중세 서유럽의 형성','유럽·아메리카',3),(20,'비잔티움 제국·십자군·중세 말','유럽·아메리카',3),(21,'르네상스와 종교 개혁','유럽·아메리카',3),(22,'신항로 개척과 절대 왕정','유럽·아메리카',3),(23,'영국 혁명과 미국 혁명','유럽·아메리카',3),(24,'프랑스 혁명과 나폴레옹','유럽·아메리카',3),(25,'산업 혁명과 국민 국가의 형성','유럽·아메리카',3),
 (26,'제국주의와 아프리카·태평양 분할','제국주의·세계 대전',4),(27,'동아시아의 근대화 운동','제국주의·세계 대전',4),(28,'서아시아·인도·동남아시아의 민족 운동','제국주의·세계 대전',4),(29,'제1차 세계 대전과 러시아 혁명','제국주의·세계 대전',4),(30,'전간기와 아시아의 민족 운동','제국주의·세계 대전',4),(31,'제2차 세계 대전','제국주의·세계 대전',4),
 (32,'냉전과 탈냉전','현대 세계',4),(33,'제3세계와 현대 아시아·아프리카','현대 세계',4),(34,'현대 세계의 변화와 세계 시사','현대 세계',4),
]
ERAS = ['문명의 발생','동아시아','서아시아·인도','유럽·아메리카','제국주의·세계 대전','현대 세계']
trend = {}
tp = os.path.join(D, 'trend.json')
if os.path.exists(tp): trend = json.load(open(tp, encoding='utf-8')).get('byCh', {})

chapters = []; G = {}; A = {}; EX = []; QI = []
for no, title, era, stage in PLAN:
    p = os.path.join(D, f'ch{no:02d}.json')
    row = {'no': no, 'title': title, 'era': era, 'stage': stage, 'ready': False, 'nq': 0, 'ne': 0, 'ni': 0, 'ng': 0, 'ns': 0, 'nt': trend.get(str(no), 0)}
    if os.path.exists(p):
        d = json.load(open(p, encoding='utf-8'))
        row.update({'ready': True, 'title': d['title'], 'nq': len(d['q']), 'ne': len(d['exam']), 'ni': len(d['images']), 'ng': len(d['g']), 'ns': len(d.get('essay', []))})
        for k, v in d['g'].items():
            e = dict(v); e['chs'] = sorted(set((G.get(k, {}).get('chs') or []) + [no]))
            e['img'] = [dict(d['images'][i], ch=no) for i in v.get('img', []) if i in d['images']][:1]
            if k in G:  # keep the richer entry, merge chapters
                old = G[k]; e['chs'] = sorted(set(old['chs'] + [no]))
                if len(json.dumps(old, ensure_ascii=False)) >= len(json.dumps(e, ensure_ascii=False)): old['chs'] = e['chs']; continue
            G[k] = e
        for a, t in d['alias'].items():
            if a not in A: A[a] = t
        for ex in d['exam']: EX.append({'id': ex['id'], 'ch': no, 'src': ex['src'], 'stem': ex['stem'], 'kw': ex['kw']})
        for q in d['q']: QI.append({'k': f'{no:02d}:{q["n"]}', 'ch': no, 'n': q['n'], 't': re.sub(r'\{\{(.+?)\}\}', r'\1', q['text']) + ' ' + ' '.join(q.get('kw', []))})
    chapters.append(row)
# drop aliases that point to a term that later got absorbed/missing
A = {a: t for a, t in A.items() if t in G and a not in G}
json.dump({'eras': ERAS, 'chapters': chapters, 'pages': {}}, open(os.path.join(D, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
json.dump({'g': G, 'alias': A}, open(os.path.join(D, 'glossary.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
json.dump(EX, open(os.path.join(D, 'exam_all.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
json.dump(QI, open(os.path.join(D, 'qindex.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
r = [c for c in chapters if c['ready']]
print(f"ready {len(r)}/34 · q {sum(c['nq'] for c in r)} · exam {len(EX)} · essay {sum(c['ns'] for c in r)} · images {sum(c['ni'] for c in r)} · glossary {len(G)} (alias {len(A)})")
