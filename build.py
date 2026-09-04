# -*- coding: utf-8 -*-
"""
build.py — 读取 full_total.json，归一化 5 套异构字段，
内联生成单文件 index.html（中法对照古典语料库浏览站）。

用法: python build.py
输出: index.html （双击即可在浏览器打开，或上传至任意静态托管）
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# 典籍展示顺序
CORPUS_ORDER = ['尚书', '诗经', '礼记', '春秋', '易经']

# 尚书各部
SHANGSHU_BOOKS = {'虞书', '夏书', '商书', '周书'}
SHANGSHU_BOOK_ORDER = {'虞书': 0, '夏书': 1, '商书': 2, '周书': 3}

# 春秋十二公传统次序（隐/桓/庄/闵/僖/文/宣/成/襄/昭/定/哀）
CHUNQIU_DUKE_ORDER = {
    '隐公': 0, '桓公': 1, '庄公': 2, '闵公': 3, '僖公': 4, '文公': 5,
    '宣公': 6, '成公': 7, '襄公': 8, '昭公': 9, '定公': 10, '哀公': 11,
}

# 数据源：full_total.json（尚书/诗经/礼记 + 旧占位）+ 独立完整语料
SRC_MAIN = os.path.join(HERE, 'full_total.json')
SRC_CHUNQIU = os.path.join(HERE, 'chunqiu_corpus.json (JSON结构化数据).json')
SRC_YIJING = os.path.join(HERE, '古籍语料库', 'data', 'database', '易经_corpus.db')
OUT = os.path.join(HERE, 'index.html')


def to_int(v, default=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def normalize(d):
    """把一条原始记录归一化为统一结构。"""
    book = d.get('book')

    # 1) 礼记：cn_sentence / fr_sentence
    if 'cn_sentence' in d:
        ch = d.get('chapter') or ''
        try:
            ch_label = f"第 {int(ch)} 条"
        except (ValueError, TypeError):
            ch_label = str(ch)
        return {
            'corpus': '礼记',
            'book': '',
            'chapter': ch_label,
            'zh': d.get('cn_sentence', '') or '',
            'fr': d.get('fr_sentence', '') or '',
            'src': d.get('source', '') or '',
            'meta': '',
            'sort': to_int(d.get('corpus_id')),
            'book_sort': 0,
            'chapter_sort': to_int(ch, 9999),
        }

    # 2) 诗经
    if book == '诗经':
        return {
            'corpus': '诗经',
            'book': '',
            'chapter': d.get('chapter', '') or '',
            'zh': d.get('chinese', '') or '',
            'fr': d.get('french', '') or '',
            'src': d.get('source', '') or d.get('sourse', '') or '',
            'meta': '',
            'sort': to_int(d.get('id_sub')),
            'book_sort': 0,
            'chapter_sort': to_int(d.get('id_sub'), 9999),
        }

    # 3) 尚书（虞/夏/商/周书）
    if book in SHANGSHU_BOOKS:
        return {
            'corpus': '尚书',
            'book': book,
            'chapter': d.get('chapter', '') or '',
            'zh': d.get('chinese', '') or '',
            'fr': d.get('french', '') or '',
            'src': d.get('sourse', '') or '',
            'meta': '',
            'sort': to_int(d.get('id_sub')),
            'book_sort': SHANGSHU_BOOK_ORDER.get(book, 99),
            'chapter_sort': to_int(d.get('id_sub'), 9999),
        }

    # 4) 春秋（十二公 → 年）
    if book == '春秋':
        duke = d.get('duke_cn', '') or ''
        meta_parts = []
        if d.get('juan'):
            meta_parts.append(d['juan'])
        if d.get('duke_fr'):
            meta_parts.append(d['duke_fr'])
        if d.get('year_fr'):
            meta_parts.append(d['year_fr'])
        if d.get('year_bc'):
            meta_parts.append(f"公元前 {d['year_bc']}")
        return {
            'corpus': '春秋',
            'book': duke,
            'chapter': d.get('year_cn', '') or '',
            'zh': d.get('chinese', '') or '',
            'fr': d.get('french', '') or '',
            'src': "春秋（顾赛芬法译本：Tch'ouen Ts'iou / Séraphin Couvreur）",
            'meta': ' · '.join(meta_parts),
            'sort': to_int(d.get('id')),
            'book_sort': CHUNQIU_DUKE_ORDER.get(duke, 99),
            'chapter_sort': to_int(d.get('seq_in_juan')),
        }

    # 5) 易经（六十四卦）
    if book == '易经':
        hx = d.get('hexagram', '') or ''
        chap = f"{hx}卦" if hx else ''
        meta_parts = []
        if d.get('type'):
            meta_parts.append(d['type'])
        if d.get('position'):
            meta_parts.append(d['position'])
        if d.get('keywords'):
            meta_parts.append(str(d['keywords']))
        return {
            'corpus': '易经',
            'book': '',
            'chapter': chap,
            'zh': d.get('chinese', '') or '',
            'fr': d.get('french', '') or '',
            'src': '易经（顾赛芬法译本：Y King / Séraphin Couvreur）',
            'meta': ' · '.join(meta_parts),
            'sort': to_int(d.get('id'), 9999),
            'book_sort': 0,
            'chapter_sort': to_int(d.get('hexagram_no'), 9999),
        }

    # 兜底
    return {
        'corpus': str(book or '其他'),
        'book': '',
        'chapter': d.get('chapter', '') or '',
        'zh': d.get('chinese', '') or d.get('cn_sentence', '') or '',
        'fr': d.get('french', '') or d.get('fr_sentence', '') or '',
        'src': d.get('source', '') or d.get('sourse', '') or '',
        'meta': '',
        'sort': 0,
        'book_sort': 0,
        'chapter_sort': 0,
    }


def load_all():
    """聚合所有数据源：full_total.json（去春秋/易经旧占位）+ 春秋独立 JSON + 易经 SQLite。"""
    raw = []
    # 1) full_total.json：跳过春秋/易经占位（各 1 条），由独立完整语料取代
    with open(SRC_MAIN, 'r', encoding='utf-8') as f:
        main = json.load(f)
    skipped = 0
    for d in main:
        if d.get('book') in ('春秋', '易经'):
            skipped += 1
            continue
        raw.append(d)
    print(f"  full_total.json：{len(main)} 条（跳过春秋/易经占位 {skipped} 条）")

    # 2) 春秋完整语料（JSON）
    if os.path.exists(SRC_CHUNQIU):
        with open(SRC_CHUNQIU, 'r', encoding='utf-8') as f:
            cq = json.load(f)
        raw.extend(cq)
        print(f"  春秋 chunqiu_corpus.json：{len(cq)} 条")
    else:
        print("  [警告] 未找到 春秋 语料：", SRC_CHUNQIU)

    # 3) 易经完整语料（SQLite）
    if os.path.exists(SRC_YIJING):
        import sqlite3
        con = sqlite3.connect(SRC_YIJING)
        cur = con.cursor()
        cols = [r[1] for r in cur.execute("PRAGMA table_info(corpus)")]
        rows = cur.execute(f"SELECT {','.join(cols)} FROM corpus").fetchall()
        con.close()
        yj = [dict(zip(cols, row)) for row in rows]
        raw.extend(yj)
        print(f"  易经 易经_corpus.db：{len(yj)} 条")
    else:
        print("  [警告] 未找到 易经 语料：", SRC_YIJING)

    # 4) 自定义扩充语料（JSON）
    src_custom = os.path.join(HERE, 'custom_corpus.json')
    if os.path.exists(src_custom):
        with open(src_custom, 'r', encoding='utf-8') as f:
            custom = json.load(f)
        if not isinstance(custom, list):
            raise ValueError("custom_corpus.json 必须是 JSON 数组，例如 []")
        raw.extend(custom)
        print(f"  自定义扩充语料 custom_corpus.json：{len(custom)} 条")
    else:
        print("  [提示] 未找到自定义扩充语料：", src_custom)

    return raw


def main():
    raw = load_all()
    records = [normalize(d) for d in raw]

    # 排序：典籍顺序 -> 书(书部/公)序 -> 章节序 -> id
    order_map = {c: i for i, c in enumerate(CORPUS_ORDER)}
    records.sort(key=lambda r: (
        order_map.get(r['corpus'], 99),
        r['book_sort'],
        r['chapter_sort'],
        r['chapter'],
        r['sort'],
    ))

    # 重新编号全局 id（1..N）
    for i, r in enumerate(records, 1):
        r['id'] = i
    # 去掉临时排序键
    for r in records:
        r.pop('sort', None)
        r.pop('book_sort', None)
        r.pop('chapter_sort', None)

    data_json = json.dumps(records, ensure_ascii=False)

    html = HTML_TEMPLATE.replace('"__DATA_PLACEHOLDER__"', data_json)

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(html)

    # 统计
    from collections import Counter
    c = Counter(r['corpus'] for r in records)
    print(f"已生成 {OUT}")
    print(f"共 {len(records)} 条记录：")
    for k in CORPUS_ORDER:
        if c.get(k):
            print(f"  {k}: {c[k]} 条")
    print(f"文件大小: {os.path.getsize(OUT)/1024:.1f} KB")


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>中法对照古典语料库 · 尚书 · 诗经 · 礼记 · 春秋 · 易经</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&family=Noto+Serif:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
<style>
  :root{
    --bg:#f3ede0; --panel:#fffdf6; --ink:#2a2622; --ink-soft:#5a5048;
    --line:#d8cdb4; --accent:#9c2a1d; --accent-soft:#c75b4d;
    --hl:#fff2a8; --hl-ink:#7a1f12; --shadow:0 1px 3px rgba(60,40,20,.08);
  }
  *{box-sizing:border-box}
  html,body{margin:0;padding:0}
  body{
    background:var(--bg);
    color:var(--ink);
    font-family:"Noto Serif","Georgia","Times New Roman",serif;
    font-size:16px; line-height:1.7;
    -webkit-font-smoothing:antialiased;
  }
  .cn{font-family:"Noto Serif SC","Source Han Serif SC","STSong","SimSun",serif;}
  .fr{font-family:"Noto Serif","Georgia","Times New Roman",serif;}

  header.app{
    background:linear-gradient(180deg,#fbf6ea,#f3ede0);
    border-bottom:2px solid var(--line);
    padding:18px 26px 14px;
  }
  header.app h1{margin:0;font-size:22px;font-weight:700;letter-spacing:1px;}
  header.app h1 .seal{color:var(--accent);}
  header.app .sub{margin:4px 0 0;color:var(--ink-soft);font-size:13px;}
  header.app .stats{margin-top:8px;font-size:12px;color:var(--ink-soft);}

  .layout{display:flex;min-height:calc(100vh - 92px);}
  aside.tree{
    width:260px;flex:0 0 260px;
    background:#fbf6ea;border-right:1px solid var(--line);
    padding:14px 10px 40px;overflow-y:auto;max-height:calc(100vh - 92px);
    position:sticky;top:0;
  }
  aside.tree h2{font-size:12px;color:var(--ink-soft);margin:14px 6px 6px;letter-spacing:2px;text-transform:uppercase;}
  .corpus{margin-bottom:4px;}
  .corpus > .label,.node{
    display:flex;align-items:center;gap:6px;
    padding:5px 8px;border-radius:5px;cursor:pointer;
    font-size:15px;color:var(--ink);
    user-select:none;
  }
  .corpus > .label:hover,.node:hover{background:rgba(156,42,29,.07);}
  .corpus > .label .caret{font-size:10px;color:var(--ink-soft);transition:transform .15s;}
  .corpus.open > .label .caret{transform:rotate(90deg);}
  .corpus > .label .name{font-weight:600;}
  .corpus > .label .cnt{margin-left:auto;font-size:11px;color:var(--ink-soft);background:rgba(0,0,0,.05);padding:0 6px;border-radius:8px;}
  .sublist{display:none;margin:2px 0 4px 12px;}
  .corpus.open .sublist{display:block;}
  .sublist .book > .label{font-weight:600;color:var(--ink);}
  .sublist .book > .label .caret{font-size:9px;color:var(--ink-soft);transition:transform .15s;}
  .sublist .book.open > .label .caret{transform:rotate(90deg);}
  .sublist .book .chapters{display:none;margin:2px 0 4px 14px;}
  .sublist .book.open .chapters{display:block;}
  .node{font-size:14px;font-weight:400;}
  .node.active,.corpus > .label.active{background:var(--accent);color:#fff;}
  .node.active .cnt,.corpus > .label.active .cnt{background:rgba(255,255,255,.25);color:#fff;}
  .sublist.scroll{max-height:260px;overflow-y:auto;}

  main.view{flex:1 1 auto;padding:20px 26px 60px;min-width:0;}
  .toolbar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:14px;}
  .searchwrap{flex:1 1 360px;display:flex;min-width:260px;}
  .searchwrap input{
    flex:1;padding:9px 12px;font-size:15px;font-family:inherit;
    border:1px solid var(--line);border-right:none;border-radius:6px 0 0 6px;
    background:#fffdf6;outline:none;
  }
  .searchwrap input:focus{border-color:var(--accent-soft);}
  .searchwrap button{
    padding:9px 16px;border:1px solid var(--accent);background:var(--accent);color:#fff;
    border-radius:0 6px 6px 0;cursor:pointer;font-size:14px;font-family:inherit;
  }
  .searchwrap button:hover{background:var(--accent-soft);}
  .seg{display:inline-flex;border:1px solid var(--line);border-radius:6px;overflow:hidden;background:#fffdf6;}
  .seg button{
    border:none;background:transparent;padding:7px 12px;font-size:13px;cursor:pointer;
    font-family:inherit;color:var(--ink-soft);
  }
  .seg button.on{background:var(--accent);color:#fff;}
  .clearbtn{
    border:1px solid var(--line);background:#fffdf6;padding:7px 12px;border-radius:6px;
    cursor:pointer;font-size:13px;color:var(--ink-soft);font-family:inherit;
  }
  .clearbtn:hover{color:var(--accent);}

  .crumb{font-size:13px;color:var(--ink-soft);margin-bottom:6px;}
  .crumb b{color:var(--ink);}
  .resultcount{font-size:13px;color:var(--ink-soft);margin:0 0 12px;}

  .card{
    background:var(--panel);border:1px solid var(--line);border-radius:8px;
    box-shadow:var(--shadow);padding:16px 18px;margin:0 0 14px;
  }
  .card .head{display:flex;flex-wrap:wrap;gap:8px 14px;align-items:baseline;
    border-bottom:1px dashed var(--line);padding-bottom:8px;margin-bottom:12px;}
  .card .head .no{font-size:12px;color:var(--ink-soft);}
  .card .head .where{font-size:14px;font-weight:600;color:var(--accent);}
  .card .head .where .sep{color:var(--ink-soft);font-weight:400;margin:0 4px;}
  .card .head .src{margin-left:auto;font-size:11px;color:var(--ink-soft);max-width:55%;text-align:right;}
  .card .head .meta{font-size:12px;color:var(--ink-soft);font-style:italic;}
  .pair{display:grid;grid-template-columns:1fr 1fr;gap:0;border-top:1px solid transparent;}
  .pair .col{padding:2px 14px 2px 0;}
  .pair .col + .col{border-left:1px solid var(--line);padding-left:14px;}
  .pair .lang{font-size:11px;color:var(--accent);letter-spacing:1px;margin-bottom:4px;font-weight:600;}
  .pair .txt{font-size:17px;line-height:1.85;}
  .pair .txt.cn{font-size:18px;letter-spacing:.5px;}
  mark{background:var(--hl);color:var(--hl-ink);border-radius:2px;padding:0 1px;}
  .morewrap{display:flex;justify-content:center;padding:10px 0;}
  .morebtn{
    border:1px solid var(--line);background:var(--panel);padding:9px 22px;border-radius:6px;
    cursor:pointer;font-size:14px;color:var(--ink);font-family:inherit;
  }
  .morebtn:hover{border-color:var(--accent);color:var(--accent);}
  .empty{text-align:center;color:var(--ink-soft);padding:50px 10px;font-size:15px;}
  .empty .big{font-size:40px;margin-bottom:8px;opacity:.4;}

  footer.app{text-align:center;padding:18px;font-size:12px;color:var(--ink-soft);border-top:1px solid var(--line);}

  @media (max-width:760px){
    .layout{flex-direction:column;}
    aside.tree{position:static;width:auto;max-height:none;border-right:none;border-bottom:1px solid var(--line);}
    .pair{grid-template-columns:1fr;}
    .pair .col + .col{border-left:none;border-top:1px solid var(--line);padding-left:0;padding-top:8px;margin-top:6px;}
    .card .head .src{margin-left:0;text-align:left;max-width:100%;}
    main.view{padding:16px;}
  }

  /* ============ 门户首页 ============ */
  #portal{max-width:1080px;margin:0 auto;padding:30px 22px 50px;}
  .portal-hero{text-align:center;padding:46px 16px 24px;}
  .portal-hero h1{font-size:38px;font-weight:700;letter-spacing:3px;margin:0;}
  .portal-hero h1 .seal{color:var(--accent);}
  .portal-hero .sub{margin:10px 0 0;color:var(--ink-soft);font-size:14px;letter-spacing:2px;}
  .portal-search{display:flex;justify-content:center;gap:8px;margin:26px auto 8px;max-width:640px;}
  .portal-search input{
    flex:1;padding:13px 16px;font-size:16px;font-family:inherit;
    border:1px solid var(--line);border-radius:8px;background:var(--panel);color:var(--ink);
  }
  .portal-search input:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px rgba(156,42,29,.10);}
  .portal-search button{
    padding:13px 28px;font-size:15px;font-family:inherit;font-weight:600;letter-spacing:2px;
    border:none;border-radius:8px;background:var(--accent);color:#fff;cursor:pointer;
  }
  .portal-search button:hover{background:var(--accent-soft);}
  .portal-hint{color:var(--ink-soft);font-size:12px;margin-top:8px;}

  .boxes{display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin:36px 0 10px;}
  .box{
    display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;
    padding:26px 14px;min-height:182px;text-decoration:none;color:var(--ink);
    border:1px solid var(--line);border-radius:12px;position:relative;cursor:pointer;
    background:linear-gradient(180deg,#fffdf6,#f7f0df);transition:all .18s;
  }
  .box:hover{border-color:var(--accent);box-shadow:0 6px 18px rgba(120,60,30,.14);transform:translateY(-3px);}
  .box-cn{font-size:30px;font-weight:700;letter-spacing:4px;color:var(--accent);}
  .box-fr{margin-top:8px;font-size:11px;color:var(--ink-soft);line-height:1.5;font-style:italic;}
  .box-cnt{margin-top:12px;font-size:12px;color:var(--ink-soft);background:rgba(0,0,0,.05);padding:3px 12px;border-radius:10px;}
  .box-go{margin-top:14px;font-size:13px;color:var(--accent);font-weight:600;}

  .intro{margin:46px auto 0;max-width:880px;padding:26px 32px;background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:8px;}
  .intro h2{margin:0 0 14px;font-size:18px;color:var(--accent);letter-spacing:2px;}
  .intro p{margin:0 0 12px;font-size:14.5px;line-height:1.95;color:var(--ink);}
  .intro p:last-child{margin-bottom:0;}
  .intro .feat{color:var(--accent);font-weight:600;}

  .backbtn{
    float:right;padding:6px 14px;margin:4px 0 0;font-size:13px;font-family:inherit;
    border:1px solid var(--line);border-radius:6px;background:var(--panel);color:var(--ink);cursor:pointer;
  }
  .backbtn:hover{border-color:var(--accent);color:var(--accent);}
  #hdrScope{color:var(--ink-soft);font-weight:400;font-size:20px;}

  @media (max-width:860px){
    .boxes{grid-template-columns:repeat(3,1fr);}
    .portal-hero h1{font-size:30px;}
  }
  @media (max-width:560px){
    .boxes{grid-template-columns:repeat(2,1fr);}
    .portal-hero{padding:28px 10px 16px;}
    .portal-search{flex-direction:column;}
    .portal-search button{width:100%;}
    .intro{padding:18px;margin-top:30px;}
  }

/* ============================================================
   AI 助手
   ============================================================ */

.ai-float-btn {
  position: fixed;
  right: 28px;
  bottom: 28px;
  z-index: 9999;

  border: none;
  border-radius: 999px;

  padding: 13px 22px;

  background: var(--accent);
  color: white;

  font-size: 15px;
  font-family: inherit;

  cursor: pointer;

  box-shadow: 0 5px 18px rgba(0,0,0,.18);

  transition: transform .2s ease,
              box-shadow .2s ease;
}

.ai-float-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,.22);
}


.ai-panel {

  position: fixed;

  right: 28px;
  bottom: 85px;

  width: 390px;
  height: 560px;

  z-index: 10000;

  display: none;

  flex-direction: column;

  background: var(--panel);

  border: 1px solid var(--line);

  border-radius: 16px;

  overflow: hidden;

  box-shadow: 0 12px 40px rgba(0,0,0,.20);
}


.ai-panel.open {
  display: flex;
}


.ai-header {

  display: flex;

  align-items: center;
  justify-content: space-between;

  padding: 16px 18px;

  background: var(--accent);

  color: white;
}


.ai-title {
  font-size: 18px;
  font-weight: 700;
}


.ai-subtitle {
  margin-top: 2px;
  font-size: 12px;
  opacity: .85;
}


.ai-close {

  border: none;

  background: transparent;

  color: white;

  font-size: 25px;

  cursor: pointer;

  line-height: 1;
}


.ai-messages {

  flex: 1;

  overflow-y: auto;

  padding: 18px;

  background: var(--bg);
}


.ai-message {
  margin-bottom: 16px;
}


.ai-label {

  margin-bottom: 5px;

  font-size: 12px;

  font-weight: 700;

  color: var(--accent);
}


.ai-bubble {

  display: inline-block;

  max-width: 90%;

  padding: 10px 13px;

  border-radius: 12px;

  background: var(--panel);

  border: 1px solid var(--line);

  line-height: 1.65;

  white-space: pre-wrap;

  word-break: break-word;
}


.ai-message-user {
  text-align: right;
}


.ai-message-user .ai-label {
  color: var(--ink-soft);
}


.ai-message-user .ai-bubble {

  background: var(--accent);

  color: white;

  border: none;

  text-align: left;
}


.ai-input-area {

  display: flex;

  gap: 8px;

  padding: 12px;

  background: var(--panel);

  border-top: 1px solid var(--line);
}


#aiInput {

  flex: 1;

  resize: none;

  border: 1px solid var(--line);

  border-radius: 10px;

  padding: 10px;

  font-family: inherit;

  font-size: 14px;

  line-height: 1.5;

  outline: none;

  background: white;

  color: var(--ink);
}


#aiInput:focus {
  border-color: var(--accent-soft);
}


#aiSendBtn {

  align-self: flex-end;

  border: none;

  border-radius: 10px;

  padding: 10px 15px;

  background: var(--accent);

  color: white;

  font-family: inherit;

  cursor: pointer;
}


#aiSendBtn:disabled {

  opacity: .55;

  cursor: not-allowed;
}


@media (max-width: 600px) {

  .ai-panel {

    right: 10px;
    bottom: 75px;

    width: calc(100vw - 20px);

    height: 70vh;
  }

  .ai-float-btn {

    right: 15px;
    bottom: 15px;
  }

}

</style>
</head>
<body>

<!-- ============ 门户首页 ============ -->
<section id="portal" class="portal">
  <div class="portal-hero">
    <h1><span class="seal">中法对照</span>古典语料库</h1>
    <div class="sub">五经 · 诗 · 书 · 礼 · 易 · 春秋</div>
    <form class="portal-search" id="portalSearch">
      <input id="portalQ" type="search" placeholder="检索五经中法对照语料（中文 / Français）…" autocomplete="off">
      <button type="submit">搜索</button>
    </form>
    <div class="portal-hint">回车跨五经全文检索；或从下方进入单部典籍专属站点</div>
  </div>
  <div class="boxes" id="boxes"></div>
  <div class="intro">
    <h2>关于本平台</h2>
    <p>本平台为五经专属中法对照双语语料库网站，整合《诗》《书》《礼》《易》《春秋》全套精校平行译语文本，深度对接“识典古籍”资料库，补齐古文原文考据、篇目异文参考，同时搭载前沿AI能力，打造典籍翻译科研专属工具。</p>
    <p>平台支持<span class="feat">中法双语精准句段检索</span>、<span class="feat">核心儒学术语AI深度释义</span>、<span class="feat">古籍文本异文勘核辅助</span>、<span class="feat">多版译法智能对比点评</span>四大核心功能。专为法语研习、典籍外译研究、汉学学术调研打造，兼顾原文严谨性与数字化使用效率，助力五经海外译介研究、古典文献翻译教学，搭建中华经典跨文化传播的数字化研究桥梁。</p>
  </div>

  <!-- ============ 首页 AI 智能助手 ============ -->
<div id="homeAiPanel" style="
    margin: 30px auto;
    max-width: 1100px;
    padding: 25px;
    background: #fffaf0;
    border: 1px solid #d8c7a3;
    border-radius: 16px;
">

    <h2 style="
        margin-top: 0;
        color: #8b2e1f;
    ">
        🤖 五经 AI 智能助手
    </h2>

    <p style="color:#666;">
        可用于辅助理解《诗经》《尚书》《礼记》《春秋》《易经》等古籍。
    </p>

    <textarea
        id="aiQuestion"
        placeholder="例如：请简单介绍一下《易经》中的乾卦。"
        style="
            width: 100%;
            min-height: 100px;
            padding: 12px;
            box-sizing: border-box;
            border: 1px solid #d8c7a3;
            border-radius: 10px;
            font-size: 16px;
            resize: vertical;
        "
    ></textarea>

    <button
        id="aiAskBtn"
        style="
            margin-top: 12px;
            padding: 12px 28px;
            border: none;
            border-radius: 8px;
            background: #a83221;
            color: white;
            font-size: 16px;
            cursor: pointer;
        "
    >
        发送给 AI
    </button>

    <div
        id="aiStatus"
        style="
            margin-top: 15px;
            color: #666;
        "
    ></div>

    <div
        id="aiAnswer"
        style="
            margin-top: 15px;
            padding: 18px;
            background: white;
            border-radius: 10px;
            line-height: 1.8;
            white-space: pre-wrap;
            display: none;
        "
    ></div>

</div>

</section>

<!-- ============ AI 助手 ============ -->

<button id="aiFloatBtn" class="ai-float-btn">
  ✦ AI助手
</button>

<div id="aiPanel" class="ai-panel">

  <div class="ai-header">
    <div>
      <div class="ai-title">五经 AI 助手</div>
      <div class="ai-subtitle">通义千问 · 古籍学习助手</div>
    </div>

    <button id="aiCloseBtn" class="ai-close">
      ×
    </button>
  </div>

  <div id="aiMessages" class="ai-messages">

    <div class="ai-message ai-message-ai">
      <div class="ai-label">AI</div>
      <div class="ai-bubble">
        你好！我是五经古典语料库 AI 助手。
        <br><br>
        你可以向我询问《尚书》《诗经》《礼记》《易经》《春秋》的相关问题。
      </div>
    </div>

  </div>

  <div class="ai-input-area">

    <textarea
      id="aiInput"
      placeholder="请输入你想询问的问题……"
      rows="2"
    ></textarea>

    <button id="aiSendBtn">
      发送
    </button>

  </div>

</div>

<!-- ============ 典籍浏览站点 ============ -->
<div id="browser" class="browser" style="display:none">
  <header class="app">
    <button class="backbtn" id="backBtn">← 返回首页</button>
    <h1><span class="seal">中法对照</span>古典语料库<span id="hdrScope"></span></h1>
    <div class="sub">尚书 · 诗经 · 礼记 · 春秋 · 易经 ｜ 法译主要出自 Séraphin Couvreur 顾赛芬</div>
    <div class="stats" id="stats"></div>
  </header>
  <div class="layout">
    <aside class="tree" id="tree">
      <h2>典籍目录</h2>
      <div id="treeRoot"></div>
    </aside>
    <main class="view">
      <div class="toolbar">
        <div class="searchwrap">
          <input id="q" type="search" placeholder="输入关键词，回车搜索（中文或法语）…" autocomplete="off">
          <button id="searchBtn">搜索</button>
        </div>
        <div class="seg" id="scopeSeg" title="搜索范围">
          <button data-scope="all" class="on">全部</button>
          <button data-scope="zh">中文</button>
          <button data-scope="fr">法语</button>
        </div>
        <div class="seg" id="modeSeg" title="匹配方式">
          <button data-mode="fuzzy" class="on">模糊</button>
          <button data-mode="exact">精确</button>
        </div>
        <button class="clearbtn" id="clearBtn">重置</button>
      </div>
      <div class="crumb" id="crumb"></div>
      <div class="resultcount" id="resultcount"></div>
      <div id="list"></div>
      <div class="morewrap" id="morewrap" style="display:none;">
        <button class="morebtn" id="moreBtn">显示更多 ▾</button>
      </div>
        </main>
  </div>






  <footer class="app">
    数据源：full_total.json + 春秋/易经独立语料（共 2700 条中法对照） · 由 build.py 生成
  </footer>
</div>

<script id="data" type="application/json">"__DATA_PLACEHOLDER__"</script>
<script>
(function(){
  "use strict";
  var DATA = JSON.parse(document.getElementById('data').textContent);
  var CORPUS_ORDER = ["尚书","诗经","礼记","春秋","易经"];
  // 五经门户方框（按《诗》《书》《礼》《易》《春秋》传统次序）+ hash 路由
  var CLASSICS = [
    {cn:'诗经', route:'shijing',  fr:'Shi King · Livre des Odes'},
    {cn:'尚书', route:'shangshu', fr:'Chou King · Livre des Documents'},
    {cn:'礼记', route:'liji',     fr:'Li Ki · Livre des Rites'},
    {cn:'易经', route:'yijing',   fr:'Y King · Livre des Mutations'},
    {cn:'春秋', route:'chunqiu',  fr:"Tch'ouen Ts'iou · Annales"}
  ];
  var ROUTE2CN = {};
  CLASSICS.forEach(function(c){ ROUTE2CN[c.route] = c.cn; });

  // ---- 状态 ----
  var state = {
    corpus: null,   // 选中的典籍
    book: null,     // 选中的书/卷
    chapter: null,  // 选中的篇
    q: "",
    classic: "all", // all | 诗经 | 尚书 | 礼记 | 易经 | 春秋  当前典籍站点
    scope: "all",   // all | zh | fr
    mode: "fuzzy",  // fuzzy | exact
    shown: 0
  };
  var PAGE = 20;

  // ---- 工具 ----
  function esc(s){return String(s==null?"":s).replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];});}
  function norm(s){return String(s==null?"":s).toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"");}
  function escReg(s){return String(s).replace(/[.*+?^${}()|[\]\\]/g,"\\$&");}
  function matchContains(hay, needle, fuzzy){
    if(!needle) return true;
    if(fuzzy) return norm(hay).indexOf(norm(needle)) !== -1;
    return hay.indexOf(needle) !== -1;
  }
  function highlight(text, query, fuzzy){
    if(!query) return esc(text);
    var flags = fuzzy ? "gi" : "g";
    var re;
    try{ re = new RegExp(escReg(query), flags); }catch(e){ return esc(text); }
    var out="", last=0, m;
    while((m=re.exec(text))!==null){
      out += esc(text.slice(last, m.index));
      out += "<mark>"+esc(m[0])+"</mark>";
      last = m.index + m[0].length;
      if(m.index === re.lastIndex) re.lastIndex++;
    }
    out += esc(text.slice(last));
    return out;
  }

  // ---- 树构建 ----
  function buildTree(){
    // 统计每个典籍的条目、书、篇
    var byCorpus = {};
    DATA.forEach(function(r){
      if(state.classic !== 'all' && r.corpus !== state.classic) return;
      var c = byCorpus[r.corpus] || (byCorpus[r.corpus]={records:[], books:{}});
      c.records.push(r);
      if(r.book){
        var b = c.books[r.book] || (c.books[r.book]={chapters:{}, order:Object.keys(c.books).length});
        if(r.chapter){ b.chapters[r.chapter] = (b.chapters[r.chapter]||0)+1; }
      }
    });

    var root = document.getElementById('treeRoot');
    root.innerHTML = "";
    CORPUS_ORDER.forEach(function(cn){
      var c = byCorpus[cn];
      if(!c) return;
      var wrap = document.createElement('div');
      wrap.className = 'corpus';
      if(state.classic !== 'all') wrap.classList.add('open');
      var lab = document.createElement('div');
      lab.className = 'label';
      lab.innerHTML = '<span class="caret">▶</span><span class="name cn">'+esc(cn)+'</span><span class="cnt">'+c.records.length+'</span>';
      lab.addEventListener('click', function(e){
        e.stopPropagation();
        if(e.target.classList.contains('caret') || e.target.classList.contains('name')){
          wrap.classList.toggle('open');
        }
        selectCorpus(cn, lab);
      });
      wrap.appendChild(lab);

      var sub = document.createElement('div');
      sub.className = 'sublist';

      var books = Object.keys(c.books).sort(function(a,b){
        var ba=c.books[a].order, bb=c.books[b].order; return ba-bb;
      });
      if(books.length){
        // 尚书：按书分组，书下再列篇
        books.forEach(function(bn){
          var b = c.books[bn];
          var bwrap = document.createElement('div');
          bwrap.className = 'book';
          var blab = document.createElement('div');
          blab.className = 'label';
          var cnt = 0;
          Object.keys(b.chapters).forEach(function(k){cnt+=b.chapters[k];});
          blab.innerHTML = '<span class="caret">▶</span><span class="name cn">'+esc(bn)+'</span><span class="cnt">'+cnt+'</span>';
          blab.addEventListener('click', function(e){
            e.stopPropagation();
            if(e.target.classList.contains('caret') || e.target.classList.contains('name')){
              bwrap.classList.toggle('open');
            }
            selectBook(cn, bn, blab);
          });
          bwrap.appendChild(blab);
          var chs = document.createElement('div');
          chs.className = 'chapters';
          Object.keys(b.chapters).forEach(function(ch){
            var nd = document.createElement('div');
            nd.className = 'node';
            nd.innerHTML = '<span class="cn">'+esc(ch)+'</span><span class="cnt">'+b.chapters[ch]+'</span>';
            nd.addEventListener('click', function(e){
              e.stopPropagation();
              selectChapter(cn, bn, ch, nd);
            });
            chs.appendChild(nd);
          });
          bwrap.appendChild(chs);
          sub.appendChild(bwrap);
        });
      } else {
        // 无书层级：直接列篇，若过多则折叠为"全部"
        var chapters = {};
        c.records.forEach(function(r){
          var k = r.chapter || "(无篇名)";
          chapters[k] = (chapters[k]||0)+1;
        });
        var keys = Object.keys(chapters);
        if(keys.length > 100){
          var nd = document.createElement('div');
          nd.className = 'node';
          nd.innerHTML = '<span class="cn">全部条目</span><span class="cnt">'+c.records.length+'</span>';
          nd.addEventListener('click', function(e){
            e.stopPropagation();
            selectCorpus(cn, nd);
          });
          sub.appendChild(nd);
        }else{
          sub.classList.add('scroll');
          keys.forEach(function(ch){
            var nd = document.createElement('div');
            nd.className = 'node';
            nd.innerHTML = '<span class="cn">'+esc(ch)+'</span><span class="cnt">'+chapters[ch]+'</span>';
            nd.addEventListener('click', function(e){
              e.stopPropagation();
              selectChapter(cn, null, ch, nd);
            });
            sub.appendChild(nd);
          });
        }
      }
      wrap.appendChild(sub);
      root.appendChild(wrap);
    });
  }

  function clearActive(){
    var act = document.querySelectorAll('.active');
    for(var i=0;i<act.length;i++) act[i].classList.remove('active');
  }

  function selectCorpus(cn, el){
    clearActive();
    el.classList.add('active');
    state.corpus = cn; state.book = null; state.chapter = null;
    state.shown = 0;
    render();
  }
  function selectBook(cn, bn, el){
    clearActive();
    el.classList.add('active');
    state.corpus = cn; state.book = bn; state.chapter = null;
    state.shown = 0;
    render();
  }
  function selectChapter(cn, bn, ch, el){
    clearActive();
    el.classList.add('active');
    state.corpus = cn; state.book = bn; state.chapter = ch;
    state.shown = 0;
    render();
  }

  // ---- 过滤 ----
  function currentSet(){
    var q = state.q.trim();
    if(q){
      return DATA.filter(function(r){
        if(state.classic !== 'all' && r.corpus !== state.classic) return false;
        var inZh = matchContains(r.zh, q, state.mode==='fuzzy');
        var inFr = matchContains(r.fr, q, state.mode==='fuzzy');
        if(state.scope==='zh') return inZh;
        if(state.scope==='fr') return inFr;
        return inZh || inFr;
      });
    }
    return DATA.filter(function(r){
      if(state.classic !== 'all' && r.corpus !== state.classic) return false;
      if(state.corpus && r.corpus !== state.corpus) return false;
      if(state.book && r.book !== state.book) return false;
      if(state.chapter && r.chapter !== state.chapter) return false;
      return true;
    });
  }

  function crumbText(){
    var parts = [];
    var base = state.classic !== 'all' ? state.classic : null;
    var corp = state.corpus || base;
    if(corp) parts.push(corp);
    if(state.book) parts.push(state.book);
    if(state.chapter) parts.push(state.chapter);
    return parts.length ? '当前浏览：<b>'+parts.map(esc).join(' <span class="sep">›</span> ')+'</b>' : '当前浏览：<b>全部典籍</b>';
  }

  function renderCard(r){
    var where = esc(r.corpus);
    if(r.book) where += ' <span class="sep">›</span> '+esc(r.book);
    if(r.chapter) where += ' <span class="sep">›</span> <span class="cn">'+esc(r.chapter)+'</span>';
    var src = r.src ? '<div class="src">'+esc(r.src)+'</div>' : '';
    var meta = r.meta ? '<div class="meta">'+esc(r.meta)+'</div>' : '';
    var zhHtml = highlight(r.zh, state.q.trim(), state.mode==='fuzzy');
    var frHtml = highlight(r.fr, state.q.trim(), state.mode==='fuzzy');
    return ''
      + '<div class="card">'
      +   '<div class="head">'
      +     '<span class="no">№ '+r.id+'</span>'
      +     '<span class="where">'+where+'</span>'
      +     meta
      +     src
      +   '</div>'
      +   '<div class="pair">'
      +     '<div class="col"><div class="lang">中文</div><div class="txt cn">'+zhHtml+'</div></div>'
      +     '<div class="col"><div class="lang">Français</div><div class="txt fr">'+frHtml+'</div></div>'
      +   '</div>'
      + '</div>';
  }

  function render(){
    var set = currentSet();
    document.getElementById('crumb').innerHTML = crumbText();
    var rc = document.getElementById('resultcount');
    if(state.q.trim()){
      rc.textContent = '搜索 "'+state.q.trim()+'" ：命中 '+set.length+' 条'
        + (state.scope==='zh'?' （仅中文）':state.scope==='fr'?' （仅法语）':' （中文或法语）')
        + ' · '+(state.mode==='fuzzy'?'模糊匹配':'精确匹配');
    }else{
      rc.textContent = '共 '+set.length+' 条';
    }
    var list = document.getElementById('list');
    if(set.length === 0){
      list.innerHTML = '<div class="empty"><div class="big">∅</div>没有匹配的条目</div>';
      document.getElementById('morewrap').style.display='none';
      return;
    }
    var end = Math.min(state.shown + PAGE, set.length);
    var html = "";
    for(var i=state.shown;i<end;i++) html += renderCard(set[i]);
    if(state.shown === 0) list.innerHTML = html;
    else list.insertAdjacentHTML('beforeend', html);
    state.shown = end;
    var mw = document.getElementById('morewrap');
    if(end < set.length){ mw.style.display='flex'; document.getElementById('moreBtn').textContent = '显示更多 ▾ （剩余 '+(set.length-end)+' 条）'; }
    else mw.style.display='none';
  }

  // ---- 事件 ----
  function bind(){
    var q = document.getElementById('q');
    var btn = document.getElementById('searchBtn');
    function doSearch(){
      state.q = q.value;
      state.shown = 0;
      clearActive();
      state.corpus = state.book = state.chapter = null;
      render();
    }
    btn.addEventListener('click', doSearch);
    q.addEventListener('keydown', function(e){ if(e.key==='Enter'){ e.preventDefault(); doSearch(); } });
    q.addEventListener('input', function(){
      if(q.value === '' && state.q !== ''){ state.q=''; state.shown=0; render(); }
    });

    var scope = document.getElementById('scopeSeg');
    scope.addEventListener('click', function(e){
      var b = e.target.closest('button'); if(!b) return;
      scope.querySelectorAll('button').forEach(function(x){x.classList.remove('on');});
      b.classList.add('on');
      state.scope = b.dataset.scope;
      if(state.q.trim()){ state.shown=0; render(); }
    });
    var mode = document.getElementById('modeSeg');
    mode.addEventListener('click', function(e){
      var b = e.target.closest('button'); if(!b) return;
      mode.querySelectorAll('button').forEach(function(x){x.classList.remove('on');});
      b.classList.add('on');
      state.mode = b.dataset.mode;
      if(state.q.trim()){ state.shown=0; render(); }
    });

    document.getElementById('moreBtn').addEventListener('click', function(){ render(); });
    document.getElementById('clearBtn').addEventListener('click', function(){
      q.value=''; state.q=''; state.shown=0;
      state.corpus=state.book=state.chapter=null;
      clearActive();
      render();
    });
  }

  // ---- 门户与路由 ----
  function buildBoxes(){
    var stats = {};
    DATA.forEach(function(r){ stats[r.corpus] = (stats[r.corpus]||0)+1; });
    var boxes = document.getElementById('boxes');
    boxes.innerHTML = '';
    CLASSICS.forEach(function(c){
      var n = stats[c.cn]||0;
      var a = document.createElement('a');
      a.className = 'box';
      a.href = '#'+c.route;
      a.innerHTML = '<div class="box-cn cn">'+esc(c.cn)+'</div>'
        + '<div class="box-fr">'+esc(c.fr)+'</div>'
        + '<div class="box-cnt">共 '+n+' 条</div>'
        + '<div class="box-go">进入 →</div>';
      boxes.appendChild(a);
    });
  }
  function showPortal(){
    document.getElementById('portal').style.display = '';
    document.getElementById('browser').style.display = 'none';
    document.getElementById('hdrScope').textContent = '';
    document.title = '中法对照古典语料库 · 五经';
    window.scrollTo(0,0);
  }
  function showBrowser(classic, q){
    document.getElementById('portal').style.display = 'none';
    document.getElementById('browser').style.display = '';
    state.classic = classic;
    state.q = q || '';
    document.getElementById('q').value = state.q;
    state.corpus = state.book = state.chapter = null;
    state.shown = 0;
    clearActive();
    document.getElementById('hdrScope').textContent = classic === 'all' ? '' : ' · '+classic;
    document.title = (classic === 'all' ? '五经' : classic) + ' · 中法对照古典语料库';
    buildTree();
    render();
  }
  function route(){
    var h = location.hash.replace(/^#/, '');
    var q = '';
    var qi = h.indexOf('?');
    if(qi >= 0){
      try { q = decodeURIComponent(new URLSearchParams(h.slice(qi+1)).get('q') || ''); } catch(e){}
      h = h.slice(0, qi);
    }
    if(h === '' || h === 'home'){ showPortal(); return; }
    var classic = 'all';
    if(ROUTE2CN[h]){ classic = ROUTE2CN[h]; }
    else if(h !== 'all'){ showPortal(); return; }  // 未知路由回首页
    showBrowser(classic, q);
  }

    // ============================================================
  // AI 助手
  // ============================================================

  function addAIMessage(role, text) {

    var messages = document.getElementById("aiMessages");

    var wrapper = document.createElement("div");

    wrapper.className =
      role === "user"
        ? "ai-message ai-message-user"
        : "ai-message ai-message-ai";

    var label = document.createElement("div");

    label.className = "ai-label";

    label.textContent =
      role === "user" ? "你" : "AI";

    var bubble = document.createElement("div");

    bubble.className = "ai-bubble";

    bubble.textContent = text;

    wrapper.appendChild(label);

    wrapper.appendChild(bubble);

    messages.appendChild(wrapper);

    messages.scrollTop = messages.scrollHeight;

    return bubble;
  }


  async function askAI() {

    var input = document.getElementById("aiInput");

    var sendBtn = document.getElementById("aiSendBtn");

    var question = input.value.trim();

    if (!question) {
      return;
    }

    // 显示用户问题
    addAIMessage("user", question);

    input.value = "";

    sendBtn.disabled = true;

    sendBtn.textContent = "思考中…";

    // 添加临时 AI 消息
    var answerBubble =
      addAIMessage("ai", "正在请求通义千问……");

    try {

      var response = await fetch(
        "/api/ask",
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json"
          },

          body: JSON.stringify({
            question: question
          })
        }
      );

      var data = await response.json();

      if (!response.ok) {

        throw new Error(
          data.error ||
          "AI 服务请求失败"
        );

      }

      if (data.answer) {

        answerBubble.textContent =
          data.answer;

      } else {

        answerBubble.textContent =
          "AI 没有返回有效回答。";

      }

    } catch (error) {

      console.error(error);

      answerBubble.textContent =
        "❌ AI 服务连接失败。\n\n" +
        "请确认：\n" +
        "1. ai_server.py 正在运行；\n" +
        "2. AI 服务地址为 http://127.0.0.1:5001；\n" +
        "3. DASHSCOPE_API_KEY 已正确配置。";

    } finally {

      sendBtn.disabled = false;

      sendBtn.textContent = "发送";
    }
  }

  async function askHomeAI() {
  var input = document.getElementById("aiQuestion");
  var sendBtn = document.getElementById("aiAskBtn");
  var status = document.getElementById("aiStatus");
  var answer = document.getElementById("aiAnswer");

  var question = input.value.trim();

  if (!question) {
    status.style.display = "block";
    status.textContent = "请输入你的问题。";
    return;
  }

  sendBtn.disabled = true;
  sendBtn.textContent = "思考中…";

  status.style.display = "block";
  status.textContent = "正在连接 AI 服务……";

  answer.style.display = "block";
  answer.textContent = "";

  try {
    var response = await fetch(
      "/api/ask",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          question: question
        })
      }
    );

    var data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "AI 服务请求失败");
    }

    answer.textContent =
      data.answer ||
      data.response ||
      data.message ||
      "AI 没有返回有效回答。";

    status.textContent = "回答完成";

  } catch (error) {
    console.error(error);

    status.textContent = "AI 服务连接失败";

    answer.textContent =
      "抱歉，AI 暂时无法回答。\n\n" +
      "请稍后再试。";
  } finally {
    sendBtn.disabled = false;
    sendBtn.textContent = "发送给 AI";
  }
}


  function bindAI() {

    var openBtn =
      document.getElementById("aiFloatBtn");

    var closeBtn =
      document.getElementById("aiCloseBtn");

    var panel =
      document.getElementById("aiPanel");

    var input =
      document.getElementById("aiInput");

    var sendBtn =
      document.getElementById("aiSendBtn");


    openBtn.addEventListener(
      "click",
      function() {

        panel.classList.add("open");

        input.focus();

      }
    );


    closeBtn.addEventListener(
      "click",
      function() {

        panel.classList.remove("open");

      }
    );


    sendBtn.addEventListener(
      "click",
      askAI
    );


    input.addEventListener(
      "keydown",
      function(e) {

        if (
          e.key === "Enter" &&
          !e.shiftKey
        ) {

          e.preventDefault();

          askAI();

        }

      }
    );

  }

  // ---- 初始化 ----
  function init(){
    var stats = {};
    DATA.forEach(function(r){ stats[r.corpus] = (stats[r.corpus]||0)+1; });
    var parts = CORPUS_ORDER.filter(function(c){return stats[c];}).map(function(c){return c+' '+stats[c];});
    document.getElementById('stats').textContent = '共 '+DATA.length+' 条 ｜ '+parts.join(' ｜ ');
    buildBoxes();
    bind();
    bindAI();
    document.getElementById("aiAskBtn").addEventListener("click", askHomeAI);
    document.getElementById('portalSearch').addEventListener('submit', function(e){
      e.preventDefault();
      var v = document.getElementById('portalQ').value.trim();
      location.hash = 'all?q=' + encodeURIComponent(v);
    });
    document.getElementById('backBtn').addEventListener('click', function(){
      location.hash = 'home';
    });
    window.addEventListener('hashchange', route);
    route();
  }

  init();
})();
</script>
</body>
</html>
"""


if __name__ == '__main__':
    main()
