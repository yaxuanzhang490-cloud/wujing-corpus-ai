import pandas as pd
import sqlite3
from pathlib import Path

# ============================================================
# 《易经》古籍语料库 SQLite 数据库构建
# ============================================================

print("=" * 60)
print("开始构建《易经》SQLite 数据库")
print("=" * 60)


# ============================================================
# 1. 设置路径
# ============================================================

BASE_DIR = Path(__file__).parent.parent

excel_path = BASE_DIR / "data" / "易经_结构化工作版.xlsx"

database_dir = BASE_DIR / "data" / "database"

database_dir.mkdir(parents=True, exist_ok=True)

db_path = database_dir / "易经_corpus.db"


print(f"\nExcel 文件：{excel_path}")
print(f"数据库文件：{db_path}")


# ============================================================
# 2. 检查 Excel
# ============================================================

if not excel_path.exists():
    print("\n❌ 找不到 Excel 文件！")
    print(excel_path)
    exit()

print("\n✓ Excel 文件存在")


# ============================================================
# 3. 读取 Excel
# ============================================================

df = pd.read_excel(
    excel_path,
    sheet_name="structured_corpus"
)

print(f"✓ 成功读取 {len(df)} 条数据")


# ============================================================
# 4. 删除旧数据库（如果存在）
# ============================================================

if db_path.exists():
    print("\n⚠ 检测到旧数据库")
    print("正在删除旧数据库并重新构建……")
    db_path.unlink()


# ============================================================
# 5. 创建 SQLite 数据库
# ============================================================

conn = sqlite3.connect(db_path)

print("\n✓ SQLite 数据库连接成功")


# ============================================================
# 6. 创建 corpus 表
# ============================================================

create_table_sql = """
CREATE TABLE corpus (

    id INTEGER PRIMARY KEY,

    book TEXT NOT NULL,

    hexagram_no INTEGER NOT NULL,

    hexagram TEXT NOT NULL,

    type TEXT NOT NULL,

    position TEXT,

    chinese TEXT NOT NULL,

    french TEXT NOT NULL,

    keywords TEXT,

    annotation TEXT,

    data_check TEXT

);
"""

conn.execute(create_table_sql)

print("✓ corpus 数据表创建成功")


# ============================================================
# 7. 写入数据
# ============================================================

df.to_sql(
    "corpus",
    conn,
    if_exists="append",
    index=False
)

print(f"✓ 成功写入 {len(df)} 条语料")


# ============================================================
# 8. 创建常用索引
# ============================================================

print("\n正在创建数据库索引……")

conn.execute("""
CREATE INDEX idx_hexagram_no
ON corpus(hexagram_no);
""")

conn.execute("""
CREATE INDEX idx_hexagram
ON corpus(hexagram);
""")

conn.execute("""
CREATE INDEX idx_type
ON corpus(type);
""")

conn.execute("""
CREATE INDEX idx_position
ON corpus(position);
""")

print("✓ 数据库索引创建完成")


# ============================================================
# 9. 数据库验证
# ============================================================

print("\n正在验证数据库……")

cursor = conn.cursor()

cursor.execute(
    "SELECT COUNT(*) FROM corpus"
)

total = cursor.fetchone()[0]

print(f"数据库记录数：{total}")


cursor.execute("""
SELECT COUNT(DISTINCT hexagram_no)
FROM corpus
""")

hexagram_count = cursor.fetchone()[0]

print(f"数据库卦数：{hexagram_count}")


cursor.execute("""
SELECT type, COUNT(*)
FROM corpus
GROUP BY type
""")

print("\n数据库数据类型：")

for row in cursor.fetchall():
    print(f"  {row[0]}：{row[1]}")


# ============================================================
# 10. 测试查询
# ============================================================

print("\n正在进行查询测试……")

cursor.execute("""
SELECT
    hexagram,
    position,
    chinese,
    french
FROM corpus
WHERE chinese LIKE '%龙%'
""")

results = cursor.fetchall()

print(f"搜索「龙」：找到 {len(results)} 条")

for row in results[:5]:
    print("\n卦：", row[0])
    print("位置：", row[1])
    print("中文：", row[2])
    print("法文：", row[3])


# ============================================================
# 11. 关闭数据库
# ============================================================

conn.close()

print("\n✓ 数据库连接已关闭")


# ============================================================
# 12. 最终结果
# ============================================================

print("\n" + "=" * 60)
print("《易经》SQLite 数据库构建完成！")
print("=" * 60)

print(f"""
数据库位置：

{db_path}

总记录数：{total}
卦数：{hexagram_count}
""")

print("=" * 60)