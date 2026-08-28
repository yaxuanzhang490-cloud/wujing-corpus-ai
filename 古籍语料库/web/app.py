from flask import Flask, render_template, request
import sqlite3
from pathlib import Path
import re
import html

# ============================================================
# 《易经》法汉双语古籍语料库
# Flask 网站后端
# ============================================================

app = Flask(__name__)

# ============================================================
# 项目根目录
# ============================================================

BASE_DIR = Path(__file__).parent.parent

# SQLite 数据库
DB_PATH = BASE_DIR / "data" / "database" / "易经_corpus.db"


# ============================================================
# 数据库连接
# ============================================================

def get_db():

    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# 关键词高亮函数
# ============================================================

def highlight_keyword(text, keyword):

    if text is None:
        return ""

    text = str(text)

    if not keyword:
        return html.escape(text)

    # 先进行 HTML 转义，避免原始文本中的特殊字符
    # 被浏览器误认为 HTML
    escaped_text = html.escape(text)

    escaped_keyword = html.escape(keyword)

    # 忽略大小写进行关键词高亮
    pattern = re.compile(
        re.escape(escaped_keyword),
        re.IGNORECASE
    )

    highlighted_text = pattern.sub(
        lambda match: f"<mark>{match.group(0)}</mark>",
        escaped_text
    )

    return highlighted_text


# ============================================================
# 首页
# ============================================================

@app.route("/")
def index():

    conn = get_db()

    # 总语料数量
    total_count = conn.execute(
        "SELECT COUNT(*) FROM corpus"
    ).fetchone()[0]

    # 卦的数量
    hexagram_count = conn.execute(
        "SELECT COUNT(DISTINCT hexagram_no) FROM corpus"
    ).fetchone()[0]

    # 卦辞数量
    guaci_count = conn.execute(
        "SELECT COUNT(*) FROM corpus WHERE type = '卦辞'"
    ).fetchone()[0]

    # 普通爻辞数量
    yao_count = conn.execute(
        "SELECT COUNT(*) FROM corpus WHERE type = '爻辞'"
    ).fetchone()[0]

    # 特殊爻辞数量
    special_count = conn.execute(
        "SELECT COUNT(*) FROM corpus WHERE type = '特殊爻辞'"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "index.html",
        total_count=total_count,
        hexagram_count=hexagram_count,
        guaci_count=guaci_count,
        yao_count=yao_count,
        special_count=special_count
    )


# ============================================================
# 搜索
# ============================================================

@app.route("/search")
def search():

    keyword = request.args.get("q", "").strip()

    results = []

    if keyword:

        conn = get_db()

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

        conn.close()

        # ====================================================
        # 对搜索结果中的中文和法文进行关键词高亮
        # ====================================================

        highlighted_results = []

        for result in results:

            item = dict(result)

            item["chinese"] = highlight_keyword(
                item["chinese"],
                keyword
            )

            item["french"] = highlight_keyword(
                item["french"],
                keyword
            )

            highlighted_results.append(item)

        results = highlighted_results

    return render_template(
        "search.html",
        keyword=keyword,
        results=results
    )


# ============================================================
# 查看某一卦
# ============================================================

@app.route("/hexagram/<int:number>")
def hexagram(number):

    conn = get_db()

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

    results = conn.execute(
        sql,
        (number,)
    ).fetchall()

    conn.close()

    return render_template(
        "hexagram.html",
        number=number,
        results=results
    )


# ============================================================
# 启动网站
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("《易经》法汉双语语料库网站")
    print("=" * 60)

    print(f"数据库：{DB_PATH}")

    if not DB_PATH.exists():

        print("❌ 数据库不存在！")

    else:

        print("✓ 数据库文件存在")

    print("\n正在启动网站……")
    print("访问地址：http://127.0.0.1:5000")
    print("按 Ctrl + C 可以停止网站")

    app.run(
        debug=True
    )