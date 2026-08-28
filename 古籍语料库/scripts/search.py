import sqlite3
from pathlib import Path

# ============================================================
# 《易经》古籍语料库检索系统
# ============================================================

print("=" * 60)
print("《易经》古籍语料库检索系统")
print("=" * 60)

# ------------------------------------------------------------
# 1. 数据库路径
# ------------------------------------------------------------

BASE_DIR = Path(__file__).parent.parent
db_path = BASE_DIR / "data" / "database" / "易经_corpus.db"

print(f"\n数据库：{db_path}")

if not db_path.exists():
    print("❌ 找不到数据库文件！")
    exit()

print("✓ 数据库文件存在")

# ------------------------------------------------------------
# 2. 连接数据库
# ------------------------------------------------------------

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

print("✓ 数据库连接成功")


# ============================================================
# 工具函数
# ============================================================

def show_results(results):
    """显示检索结果"""

    print("\n" + "=" * 60)
    print(f"找到 {len(results)} 条结果")
    print("=" * 60)

    if len(results) == 0:
        print("没有找到相关语料。")
        return

    for i, row in enumerate(results, start=1):

        position = row["position"] if row["position"] else "卦辞"

        print(f"""
【结果 {i}】
卦号：第 {row["hexagram_no"]} 卦
卦名：{row["hexagram"]}
类型：{row["type"]}
位置：{position}

中文：
{row["chinese"]}

法文：
{row["french"]}
""")

        print("-" * 60)


# ============================================================
# 1. 全文关键词检索
# ============================================================

def keyword_search():

    keyword = input("\n请输入关键词：").strip()

    if not keyword:
        print("⚠ 搜索内容不能为空。")
        return

    sql = """
    SELECT
        id,
        hexagram_no,
        hexagram,
        type,
        position,
        chinese,
        french
    FROM corpus
    WHERE
        chinese LIKE ?
        OR french LIKE ?
    ORDER BY hexagram_no, id
    """

    pattern = f"%{keyword}%"

    results = conn.execute(
        sql,
        (pattern, pattern)
    ).fetchall()

    show_results(results)


# ============================================================
# 2. 按卦号查询
# ============================================================

def hexagram_no_search():

    value = input("\n请输入卦号（1-64）：").strip()

    try:
        number = int(value)
    except ValueError:
        print("⚠ 卦号必须是数字。")
        return

    if number < 1 or number > 64:
        print("⚠ 卦号必须在 1-64 之间。")
        return

    sql = """
    SELECT
        id,
        hexagram_no,
        hexagram,
        type,
        position,
        chinese,
        french
    FROM corpus
    WHERE hexagram_no = ?
    ORDER BY id
    """

    results = conn.execute(sql, (number,)).fetchall()

    show_results(results)


# ============================================================
# 3. 按卦名查询
# ============================================================

def hexagram_name_search():

    name = input("\n请输入卦名，例如“乾”：").strip()

    if not name:
        print("⚠ 卦名不能为空。")
        return

    sql = """
    SELECT
        id,
        hexagram_no,
        hexagram,
        type,
        position,
        chinese,
        french
    FROM corpus
    WHERE hexagram = ?
    ORDER BY id
    """

    results = conn.execute(sql, (name,)).fetchall()

    show_results(results)


# ============================================================
# 4. 按爻位查询
# ============================================================

def position_search():

    position = input(
        "\n请输入爻位，例如“初九”“九五”“上六”“用九”："
    ).strip()

    if not position:
        print("⚠ 爻位不能为空。")
        return

    sql = """
    SELECT
        id,
        hexagram_no,
        hexagram,
        type,
        position,
        chinese,
        french
    FROM corpus
    WHERE position = ?
    ORDER BY hexagram_no
    """

    results = conn.execute(sql, (position,)).fetchall()

    show_results(results)


# ============================================================
# 5. 查看全部卦名
# ============================================================

def show_all_hexagrams():

    sql = """
    SELECT DISTINCT
        hexagram_no,
        hexagram
    FROM corpus
    ORDER BY hexagram_no
    """

    results = conn.execute(sql).fetchall()

    print("\n" + "=" * 60)
    print("《易经》六十四卦")
    print("=" * 60)

    for row in results:
        print(f"{row['hexagram_no']:>2}. {row['hexagram']}")

    print("=" * 60)


# ============================================================
# 主菜单
# ============================================================

while True:

    print("\n")
    print("=" * 60)
    print("请选择检索方式")
    print("=" * 60)

    print("1. 全文关键词检索")
    print("2. 按卦号查询")
    print("3. 按卦名查询")
    print("4. 按爻位查询")
    print("5. 查看全部六十四卦")
    print("q. 退出")

    choice = input("\n请输入选项：").strip()

    if choice == "1":

        keyword_search()

    elif choice == "2":

        hexagram_no_search()

    elif choice == "3":

        hexagram_name_search()

    elif choice == "4":

        position_search()

    elif choice == "5":

        show_all_hexagrams()

    elif choice.lower() == "q":

        break

    else:

        print("⚠ 无效选项，请输入 1-5 或 q。")


# ============================================================
# 关闭数据库
# ============================================================

conn.close()

print("\n数据库连接已关闭。")
print("检索系统结束。")