import json
import sqlite3
from pathlib import Path


# ============================================================
# 五经古典语料库
# 数据标准化脚本
# ============================================================

BASE_DIR = Path(__file__).parent

# ------------------------------------------------------------
# 原始数据
# ------------------------------------------------------------

FULL_TOTAL_PATH = BASE_DIR / "full_total.json"

CHUNQIU_PATH = (
    BASE_DIR
    / "chunqiu_corpus.json (JSON结构化数据).json"
)

YIJING_DB_PATH = (
    BASE_DIR
    / "古籍语料库"
    / "data"
    / "database"
    / "易经_corpus.db"
)

# ------------------------------------------------------------
# 输出文件
# ------------------------------------------------------------

OUTPUT_PATH = BASE_DIR / "normalized_corpus.json"


# ============================================================
# 工具函数
# ============================================================

def clean_text(value):
    """
    清理字段。

    None / nan / 空字符串
    都统一转换成空字符串。
    """

    if value is None:
        return ""

    text = str(value).strip()

    if text.lower() in {
        "nan",
        "none",
        "null"
    }:
        return ""

    return text


# ============================================================
# 读取 full_total.json
# ============================================================

def load_full_total():

    print("正在读取 full_total.json……")

    if not FULL_TOTAL_PATH.exists():

        print("❌ 找不到文件：")
        print(FULL_TOTAL_PATH)

        return []

    try:

        with open(
            FULL_TOTAL_PATH,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

    except Exception as e:

        print("❌ 读取 full_total.json 失败：")
        print(e)

        return []

    print(
        f"✓ full_total.json 读取成功：{len(data)} 条"
    )

    return data


# ============================================================
# 标准化《礼记》
# ============================================================

def normalize_liji(item, index):

    return {

        "id": f"liji_{index:04d}",

        "book": "礼记",

        "chapter": clean_text(
            item.get("chapter")
        ),

        "position": "",

        "type": "正文",

        "chinese": clean_text(
            item.get("cn_sentence")
        ),

        "french": clean_text(
            item.get("fr_sentence")
        ),

        "source": clean_text(
            item.get("source")
        )

    }


# ============================================================
# 标准化《尚书》
# ============================================================

def normalize_shangshu(item, index):

    book = clean_text(
        item.get("book")
    )

    # 周书、商书、虞书、夏书
    # 都属于《尚书》
    if book in {
        "周书",
        "商书",
        "虞书",
        "夏书"
    }:

        display_book = "尚书"

    elif book:

        display_book = book

    else:

        display_book = "尚书"

    return {

        "id": f"shangshu_{index:04d}",

        "book": display_book,

        "chapter": clean_text(
            item.get("chapter")
        ),

        "position": "",

        "type": "正文",

        "chinese": clean_text(
            item.get("chinese")
        ),

        "french": clean_text(
            item.get("french")
        ),

        "source": clean_text(
            item.get("source")
            or item.get("sourse")
        )

    }


# ============================================================
# 处理 full_total.json
#
# 只保留：
#   礼记
#   尚书
#
# 忽略：
#   春秋
#   易经
# ============================================================

def normalize_full_total(data):

    normalized = []

    counters = {

        "礼记": 0,

        "尚书": 0,

        "春秋_忽略": 0,

        "易经_忽略": 0,

        "其他": 0

    }

    for item in data:

        # ----------------------------------------------------
        # 礼记
        # ----------------------------------------------------

        if "cn_sentence" in item:

            counters["礼记"] += 1

            record = normalize_liji(
                item,
                counters["礼记"]
            )

            # 只有中文和法文都存在时才加入
            if (
                record["chinese"]
                and
                record["french"]
            ):

                normalized.append(record)

            continue


        # ----------------------------------------------------
        # 易经
        # ----------------------------------------------------

        if item.get("book") == "易经":

            counters["易经_忽略"] += 1

            continue


        # ----------------------------------------------------
        # 春秋
        # ----------------------------------------------------

        if (
            item.get("book") == "春秋"
            or "year_cn" in item
        ):

            counters["春秋_忽略"] += 1

            continue


        # ----------------------------------------------------
        # 尚书
        # ----------------------------------------------------

        if "chinese" in item:

            counters["尚书"] += 1

            record = normalize_shangshu(
                item,
                counters["尚书"]
            )

            if (
                record["chinese"]
                and
                record["french"]
            ):

                normalized.append(record)

            continue


        # ----------------------------------------------------
        # 其他
        # ----------------------------------------------------

        counters["其他"] += 1

    return normalized, counters


# ============================================================
# 读取真正的《春秋》
# ============================================================

def load_chunqiu():

    print()
    print("正在读取《春秋》JSON 数据库……")

    if not CHUNQIU_PATH.exists():

        print("❌ 找不到《春秋》数据文件：")
        print(CHUNQIU_PATH)

        return []

    try:

        with open(
            CHUNQIU_PATH,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

    except Exception as e:

        print("❌ 读取《春秋》失败：")
        print(e)

        return []

    print(
        f"✓ 《春秋》原始记录：{len(data)} 条"
    )

    normalized = []

    skipped_empty = 0

    for index, item in enumerate(
        data,
        start=1
    ):

        chinese = clean_text(
            item.get("chinese")
        )

        french = clean_text(
            item.get("french")
        )

        # ----------------------------------------------------
        # 如果中文和法文都为空
        # 就不进入 RAG 语料库
        # ----------------------------------------------------

        if not chinese and not french:

            skipped_empty += 1

            continue

        normalized.append({

            "id": f"chunqiu_{index:04d}",

            "book": "春秋",

            "chapter": clean_text(
                item.get("year_cn")
            ),

            "position": "",

            "type": "正文",

            "chinese": chinese,

            "french": french,

            "source": (
                "《春秋》"
                " + "
                "Séraphin Couvreur 顾赛芬法译本"
            ),

            # ------------------------------------------------
            # 《春秋》额外信息
            # ------------------------------------------------

            "juan": clean_text(
                item.get("juan")
            ),

            "duke_cn": clean_text(
                item.get("duke_cn")
            ),

            "year_bc": item.get(
                "year_bc"
            )

        })

    print(
        f"✓ 《春秋》有效记录：{len(normalized)} 条"
    )

    print(
        f"  跳过空记录：{skipped_empty} 条"
    )

    return normalized


# ============================================================
# 读取真正的《易经》
# ============================================================

def load_yijing():

    print()
    print("正在读取《易经》SQLite 数据库……")

    if not YIJING_DB_PATH.exists():

        print("❌ 找不到《易经》数据库：")
        print(YIJING_DB_PATH)

        return []

    try:

        conn = sqlite3.connect(
            YIJING_DB_PATH
        )

        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            """
            SELECT
                id,
                book,
                hexagram_no,
                hexagram,
                type,
                position,
                chinese,
                french
            FROM corpus
            ORDER BY id
            """
        ).fetchall()

        conn.close()

    except Exception as e:

        print("❌ 读取《易经》数据库失败：")
        print(e)

        return []

    normalized = []

    skipped_empty = 0

    for row in rows:

        chinese = clean_text(
            row["chinese"]
        )

        french = clean_text(
            row["french"]
        )

        if not chinese and not french:

            skipped_empty += 1

            continue

        normalized.append({

            "id": f"yijing_{row['id']:04d}",

            "book": "易经",

            "chapter": clean_text(
                row["hexagram"]
            ),

            "position": clean_text(
                row["position"]
            ),

            "type": clean_text(
                row["type"]
            ),

            "chinese": chinese,

            "french": french,

            "source": "易经 SQLite 语料库",

            # ------------------------------------------------
            # 易经结构化信息
            # ------------------------------------------------

            "hexagram_no": row[
                "hexagram_no"
            ]

        })

    print(
        f"✓ 《易经》原始记录：{len(rows)} 条"
    )

    print(
        f"✓ 《易经》有效记录：{len(normalized)} 条"
    )

    print(
        f"  跳过空记录：{skipped_empty} 条"
    )

    return normalized


# ============================================================
# 数据质量检查
# ============================================================

def check_data(data):

    print()
    print("=" * 70)
    print("标准化数据质量检查")
    print("=" * 70)

    print(
        f"总记录数：{len(data)}"
    )

    # --------------------------------------------------------
    # 统计
    # --------------------------------------------------------

    books = {}

    empty_book = 0
    empty_chinese = 0
    empty_french = 0

    ids = set()
    duplicate_ids = []

    for item in data:

        book = clean_text(
            item.get("book")
        )

        books[book] = (
            books.get(book, 0) + 1
        )

        if not book:

            empty_book += 1

        if not clean_text(
            item.get("chinese")
        ):

            empty_chinese += 1

        if not clean_text(
            item.get("french")
        ):

            empty_french += 1

        item_id = item.get("id")

        if item_id in ids:

            duplicate_ids.append(
                item_id
            )

        ids.add(item_id)

    # --------------------------------------------------------
    # 典籍统计
    # --------------------------------------------------------

    print()
    print("【1】典籍统计")

    for book, count in books.items():

        print(
            f"  {book}: {count} 条"
        )

    # --------------------------------------------------------
    # 字段完整性
    # --------------------------------------------------------

    print()
    print("【2】字段完整性")

    print(
        f"book 为空：{empty_book} 条"
    )

    print(
        f"中文为空：{empty_chinese} 条"
    )

    print(
        f"法文为空：{empty_french} 条"
    )

    # --------------------------------------------------------
    # ID
    # --------------------------------------------------------

    print()
    print("【3】ID 检查")

    print(
        f"记录总数：{len(data)}"
    )

    print(
        f"唯一 ID 数：{len(ids)}"
    )

    print(
        f"重复 ID：{len(duplicate_ids)}"
    )

    if duplicate_ids:

        print(
            "重复 ID 前20个："
        )

        print(
            duplicate_ids[:20]
        )

    # --------------------------------------------------------
    # 易经检查
    # --------------------------------------------------------

    yijing = [
        x for x in data
        if x.get("book") == "易经"
    ]

    print()
    print("【4】《易经》检查")

    print(
        f"《易经》记录：{len(yijing)} 条"
    )

    hexagrams = set()

    for item in yijing:

        no = item.get(
            "hexagram_no"
        )

        if no is not None:

            hexagrams.add(no)

    print(
        f"《易经》卦数：{len(hexagrams)}"
    )

    if len(hexagrams) == 64:

        print(
            "✓ 64 卦完整"
        )

    else:

        print(
            "⚠ 注意：《易经》卦数不是64"
        )

    # --------------------------------------------------------
    # 春秋检查
    # --------------------------------------------------------

    chunqiu = [
        x for x in data
        if x.get("book") == "春秋"
    ]

    print()
    print("【5】《春秋》检查")

    print(
        f"《春秋》记录：{len(chunqiu)} 条"
    )

    # --------------------------------------------------------
    # 前几条
    # --------------------------------------------------------

    print()
    print("【6】前3条数据")

    for item in data[:3]:

        print()
        print(item)

    # --------------------------------------------------------
    # 最后3条
    # --------------------------------------------------------

    print()
    print("【7】最后3条数据")

    for item in data[-3:]:

        print()
        print(item)


# ============================================================
# 保存
# ============================================================

def save_data(data):

    print()
    print("正在保存标准化语料库……")

    try:

        with open(
            OUTPUT_PATH,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2
            )

    except Exception as e:

        print("❌ 保存失败：")
        print(e)

        return

    print()
    print("✓ 保存成功")

    print(
        f"输出文件：{OUTPUT_PATH}"
    )


# ============================================================
# 主程序
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("五经古典语料库 - 统一数据标准化")
    print("=" * 70)

    # --------------------------------------------------------
    # 第1步：读取 full_total
    # --------------------------------------------------------

    full_total = load_full_total()

    # --------------------------------------------------------
    # 第2步：处理礼记、尚书
    # --------------------------------------------------------

    normalized, counters = (
        normalize_full_total(
            full_total
        )
    )

    print()
    print("【full_total.json 处理结果】")

    print(
        f"礼记：{counters['礼记']} 条"
    )

    print(
        f"尚书：{counters['尚书']} 条"
    )

    print(
        f"春秋：忽略 {counters['春秋_忽略']} 条"
    )

    print(
        f"易经：忽略 {counters['易经_忽略']} 条"
    )

    print(
        f"其他：{counters['其他']} 条"
    )

    # --------------------------------------------------------
    # 第3步：加入真正的春秋
    # --------------------------------------------------------

    chunqiu = load_chunqiu()

    normalized.extend(
        chunqiu
    )

    # --------------------------------------------------------
    # 第4步：加入真正的易经
    # --------------------------------------------------------

    yijing = load_yijing()

    normalized.extend(
        yijing
    )

    # --------------------------------------------------------
    # 第5步：重新生成连续 corpus_id
    # --------------------------------------------------------

    for index, item in enumerate(
        normalized,
        start=1
    ):

        item["corpus_id"] = index

    # --------------------------------------------------------
    # 第6步：质量检查
    # --------------------------------------------------------

    check_data(
        normalized
    )

    # --------------------------------------------------------
    # 第7步：保存
    # --------------------------------------------------------

    save_data(
        normalized
    )

    print()
    print("=" * 70)
    print("✓ 五经统一语料库标准化完成")
    print("=" * 70)