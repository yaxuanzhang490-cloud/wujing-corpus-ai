#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《春秋》汉法语料库构建脚本
- 读取Excel中12卷数据
- 清洗并前向填充年代信息
- 构建SQLite数据库
- 导出JSON和CSV
"""

import pandas as pd
import sqlite3
import json
import glob
import os
import re

# 配置
WORK_DIR = "/home/user/.super_doubao/super-doubao-runtime/workspace/chunqiu_corpus"
ATTACH_DIR = "/home/user/.super_doubao/super-doubao-runtime/workspace/.sessions/38437373330095874/attachments"

# 卷名映射
BOOK_MAP = {
    'LIVRE I': ('卷一', '隐公', 'In Koung'),
    'LIVRE II': ('卷二', '桓公', 'Houan'),
    'LIVRE III': ('卷三', '庄公', 'Tchouang'),
    'LIVRE IV': ('卷四', '闵公', 'Min'),
    'LIVRE V': ('卷五', '僖公', 'Hi'),
    'LIVRE VI': ('卷六', '文公', 'Ouen'),
    'LIVRE VII': ('卷七', '宣公', 'Siuen'),
    'LIVRE VIII': ('卷八', '成公', 'Tch\'eng'),
    'LIVRE IX': ('卷九', '襄公', 'Siang'),
    'LIVRE X': ('卷十', '昭公', 'Tchao'),
    'LIVRE XI': ('卷十一', '定公', 'Ting'),
    'LIVRE XII': ('卷十二', '哀公', 'Ngai'),
}

def find_excel():
    files = glob.glob(os.path.join(ATTACH_DIR, "*.xlsx"))
    if not files:
        raise FileNotFoundError("未找到Excel文件")
    return files[0]

def parse_year(year_str):
    """解析年代字段，提取中文年代、法语年代、公元前年份"""
    if pd.isna(year_str) or not str(year_str).strip():
        return None, None, None
    s = str(year_str).strip()
    # 提取公元前年份（宽松匹配，处理各种变体）
    # 匹配 "数字 avant J.C." / "数字 avant J.-C." / "数字 avant J.C" 等
    bc_match = re.search(r'(\d+)\s*avant\s*J\.?-?C\.?', s)
    bc_year = bc_match.group(1) if bc_match else None
    # 中文年代（第一行）
    lines = [l.strip() for l in s.split('\n') if l.strip()]
    cn_year = lines[0] if lines else None
    fr_year = lines[1] if len(lines) > 1 else None
    return cn_year, fr_year, bc_year

def load_all_data(file_path):
    """读取所有卷的数据"""
    xl = pd.ExcelFile(file_path)
    all_records = []
    global_id = 1

    for sheet in xl.sheet_names:
        if sheet == '目录':
            continue
        if sheet not in BOOK_MAP:
            continue

        juan, duke_cn, duke_fr = BOOK_MAP[sheet]
        df = pd.read_excel(file_path, sheet_name=sheet)

        # 前向填充年代
        df['年代'] = df['年代'].ffill()

        current_cn_year = None
        current_fr_year = None
        current_bc = None

        for _, row in df.iterrows():
            seq = row.get('序号')
            chinois = str(row.get('Chinois', '')).strip()
            francais = str(row.get('Français', '')).strip()
            year_raw = row.get('年代')

            cn_year, fr_year, bc = parse_year(year_raw)
            if cn_year:
                current_cn_year = cn_year
                current_fr_year = fr_year
                current_bc = bc

            # 跳过空行
            if not chinois and not francais:
                continue

            record = {
                'id': global_id,
                'book': '春秋',
                'book_fr': "Tch'ouen Ts'iou",
                'juan': juan,
                'juan_fr': sheet,
                'duke_cn': duke_cn,
                'duke_fr': duke_fr,
                'seq_in_juan': int(seq) if pd.notna(seq) and str(seq).isdigit() else None,
                'year_cn': current_cn_year,
                'year_fr': current_fr_year,
                'year_bc': int(current_bc) if current_bc else None,
                'chinese': chinois,
                'french': francais,
            }
            all_records.append(record)
            global_id += 1

    return all_records

def build_sqlite(records, db_path):
    """构建SQLite数据库"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS corpus (
            id INTEGER PRIMARY KEY,
            book TEXT,
            book_fr TEXT,
            juan TEXT,
            juan_fr TEXT,
            duke_cn TEXT,
            duke_fr TEXT,
            seq_in_juan INTEGER,
            year_cn TEXT,
            year_fr TEXT,
            year_bc INTEGER,
            chinese TEXT,
            french TEXT
        )
    ''')

    # 创建全文搜索虚拟表
    c.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS corpus_fts USING fts5(
            chinese, french,
            content='corpus', content_rowid='id'
        )
    ''')

    # 插入数据
    for r in records:
        c.execute('''
            INSERT INTO corpus (id, book, book_fr, juan, juan_fr, duke_cn, duke_fr,
                               seq_in_juan, year_cn, year_fr, year_bc, chinese, french)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (r['id'], r['book'], r['book_fr'], r['juan'], r['juan_fr'],
              r['duke_cn'], r['duke_fr'], r['seq_in_juan'], r['year_cn'],
              r['year_fr'], r['year_bc'], r['chinese'], r['french']))

    # 填充FTS索引
    c.execute('''
        INSERT INTO corpus_fts (rowid, chinese, french)
        SELECT id, chinese, french FROM corpus
    ''')

    # 创建索引
    c.execute('CREATE INDEX IF NOT EXISTS idx_juan ON corpus(juan)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_duke ON corpus(duke_cn)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_year_bc ON corpus(year_bc)')

    conn.commit()
    conn.close()
    print(f"SQLite数据库已构建: {db_path} ({len(records)} 条记录)")

def export_json(records, json_path):
    """导出JSON"""
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"JSON已导出: {json_path}")

def export_csv(records, csv_path):
    """导出CSV"""
    df = pd.DataFrame(records)
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"CSV已导出: {csv_path}")

def main():
    file_path = find_excel()
    print(f"读取文件: {file_path}")

    records = load_all_data(file_path)
    print(f"共加载 {len(records)} 条记录")

    # 统计
    years = set(r['year_bc'] for r in records if r['year_bc'])
    juans = set(r['juan'] for r in records)
    print(f"覆盖年份: {min(years)}-{max(years)} BC ({len(years)} 年)")
    print(f"覆盖卷数: {len(juans)}")

    # 构建数据库
    db_path = os.path.join(WORK_DIR, "chunqiu_corpus.db")
    build_sqlite(records, db_path)

    # 导出文件
    json_path = os.path.join(WORK_DIR, "chunqiu_corpus.json")
    csv_path = os.path.join(WORK_DIR, "chunqiu_corpus.csv")
    export_json(records, json_path)
    export_csv(records, csv_path)

    print("\n=== 语料库构建完成 ===")

if __name__ == '__main__':
    main()
