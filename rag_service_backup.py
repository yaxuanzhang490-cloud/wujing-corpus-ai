import json
import sqlite3
import re
from pathlib import Path


# ============================================================
# 五经古典语料库 RAG 检索服务
#
# 当前数据源：
# 1. 尚书 JSON
# 2. 春秋 JSON
# 3. 易经 SQLite
#
# 本版本重点：
# - 更准确地识别典籍、卦名、爻位
# - 卦名查询优先返回卦辞
# - 卦名 + 爻位进行精确匹配
# - 复合问题支持多个检索目标
# - 自动去重
# - 为后续 AI 综合回答提供高质量上下文
# ============================================================


# ============================================================
# 基础路径
# ============================================================

BASE_DIR = Path(__file__).parent


# ============================================================
# 数据文件
# ============================================================

SHANGSHU_PATH = BASE_DIR / "full_total.json"

CHUNQIU_PATH = (
    BASE_DIR /
    "chunqiu_corpus.json (JSON结构化数据).json"
)

YIJING_DB_PATH = (
    BASE_DIR /
    "古籍语料库" /
    "data" /
    "database" /
    "易经_corpus.db"
)


# ============================================================
# 五经名称
# ============================================================

BOOK_NAMES = [
    "诗经",
    "诗",
    "尚书",
    "书",
    "礼记",
    "礼",
    "周易",
    "易经",
    "易",
    "春秋",
]


# ============================================================
# 六十四卦
# ============================================================

HEXAGRAM_NAMES = [
    "乾",
    "坤",
    "屯",
    "蒙",
    "需",
    "讼",
    "师",
    "比",
    "小畜",
    "履",
    "泰",
    "否",
    "同人",
    "大有",
    "谦",
    "豫",
    "随",
    "蛊",
    "临",
    "观",
    "噬嗑",
    "贲",
    "剥",
    "复",
    "无妄",
    "大畜",
    "颐",
    "大过",
    "坎",
    "离",
    "咸",
    "恒",
    "遁",
    "大壮",
    "晋",
    "明夷",
    "家人",
    "睽",
    "蹇",
    "解",
    "损",
    "益",
    "夬",
    "姤",
    "萃",
    "升",
    "困",
    "井",
    "革",
    "鼎",
    "震",
    "艮",
    "渐",
    "归妹",
    "丰",
    "旅",
    "巽",
    "兑",
    "涣",
    "节",
    "中孚",
    "小过",
    "既济",
    "未济",
]


# ============================================================
# 爻位
# ============================================================

YAO_POSITIONS = [
    "初六",
    "六二",
    "六三",
    "六四",
    "六五",
    "上六",

    "初九",
    "九二",
    "九三",
    "九四",
    "九五",
    "上九",

    "用九",
    "用六",
]


# ============================================================
# 停用词
# ============================================================

STOP_WORDS = {
    "什么",
    "怎么",
    "如何",
    "为什么",
    "哪个",
    "哪些",
    "请问",
    "请",
    "介绍",
    "介绍一下",
    "告诉我",
    "是什么意思",
    "什么意思",
    "有什么",
    "关于",
    "中的",
    "里面",
    "内容",
    "意思",
    "一下",
    "一下子",
    "一下呢",
    "是否",
    "是不是",
    "有没有",
    "可以",
    "能否",
    "帮我",
    "解释",
    "说明",
    "一下子",
    "以及",
    "并且",
    "并说明",
    "并介绍",
    "分别",
    "区别",
    "比较",
}


# ============================================================
# 加载五经语料
# ============================================================

def load_corpus():

    corpus = []


    # ========================================================
    # 1. 尚书
    # ========================================================

    if SHANGSHU_PATH.exists():

        try:

            with open(
                SHANGSHU_PATH,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)


            if isinstance(data, list):

                for item in data:

                    if not isinstance(item, dict):
                        continue


                    book = item.get(
                        "book",
                        "尚书"
                    )

                    chinese = (
                        item.get("chinese")
                        or ""
                    )

                    french = (
                        item.get("french")
                        or ""
                    )


                    # ----------------------------------------
                    # 防止明显的数据污染
                    #
                    # 如果 JSON 文件名是尚书，
                    # 但其中 book 明确写成易经，
                    # 后续仍然保留原始 book，
                    # 但 source 固定为尚书。
                    # ----------------------------------------

                    corpus.append({

                        "book": book,

                        "chapter": (
                            item.get(
                                "chapter",
                                ""
                            )
                        ),

                        "chinese": chinese,

                        "french": french,

                        "source": "尚书",

                    })


        except Exception as e:

            print(
                f"⚠️ 加载尚书语料失败：{e}"
            )


    else:

        print(
            "⚠️ 尚书语料文件不存在："
        )

        print(
            SHANGSHU_PATH
        )


    # ========================================================
    # 2. 春秋
    # ========================================================

    if CHUNQIU_PATH.exists():

        try:

            with open(
                CHUNQIU_PATH,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)


            if isinstance(data, list):

                for item in data:

                    if not isinstance(item, dict):
                        continue


                    corpus.append({

                        "book": (
                            item.get(
                                "book",
                                "春秋"
                            )
                        ),

                        "chapter": (
                            item.get(
                                "year_cn",
                                ""
                            )
                        ),

                        "chinese": (
                            item.get(
                                "chinese",
                                ""
                            )
                            or ""
                        ),

                        "french": (
                            item.get(
                                "french",
                                ""
                            )
                            or ""
                        ),

                        "source": "春秋",

                    })


        except Exception as e:

            print(
                f"⚠️ 加载春秋语料失败：{e}"
            )


    else:

        print(
            "⚠️ 春秋语料文件不存在："
        )

        print(
            CHUNQIU_PATH
        )


    # ========================================================
    # 3. 易经 SQLite
    # ========================================================

    if YIJING_DB_PATH.exists():

        try:

            conn = sqlite3.connect(
                YIJING_DB_PATH
            )

            conn.row_factory = sqlite3.Row


            rows = conn.execute(
                """
                SELECT
                    book,
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


            for row in rows:

                corpus.append({

                    "book": (
                        row["book"]
                        or "易经"
                    ),

                    "chapter": (
                        row["hexagram"]
                        or ""
                    ),

                    "type": (
                        row["type"]
                        or ""
                    ),

                    "position": (
                        row["position"]
                        or ""
                    ),

                    "chinese": (
                        row["chinese"]
                        or ""
                    ),

                    "french": (
                        row["french"]
                        or ""
                    ),

                    "source": "易经",

                })


        except Exception as e:

            print(
                f"⚠️ 加载易经数据库失败：{e}"
            )


    else:

        print(
            "⚠️ 易经数据库不存在："
        )

        print(
            YIJING_DB_PATH
        )


    return corpus


# ============================================================
# 文本规范化
# ============================================================

def normalize_text(text):

    if text is None:
        return ""

    text = str(text)

    # 去除《》
    text = text.replace("《", "")
    text = text.replace("》", "")

    # 去除常见标点
    text = text.replace(
        "，",
        ""
    )

    text = text.replace(
        "。",
        ""
    )

    text = text.replace(
        "：",
        ""
    )

    text = text.replace(
        "“",
        ""
    )

    text = text.replace(
        "”",
        ""
    )

    text = text.replace(
        "？",
        ""
    )

    text = text.replace(
        "！",
        ""
    )

    text = text.replace(
        "、",
        ""
    )

    text = text.replace(
        " ",
        ""
    )

    return text.lower()


# ============================================================
# 提取典籍
# ============================================================

def extract_books(query):

    books = []

    normalized = normalize_text(
        query
    )


    # 易经
    if (
        "易经" in normalized
        or "周易" in normalized
        or "易" in normalized
    ):

        books.append(
            "易经"
        )


    # 尚书
    if (
        "尚书" in normalized
        or "书" in normalized
    ):

        books.append(
            "尚书"
        )


    # 春秋
    if "春秋" in normalized:

        books.append(
            "春秋"
        )


    # 去重
    result = []

    for book in books:

        if book not in result:

            result.append(book)


    return result


# ============================================================
# 提取卦名
# ============================================================

def extract_hexagrams(query):

    normalized = normalize_text(
        query
    )

    found = []


    # 长卦名优先
    sorted_names = sorted(
        HEXAGRAM_NAMES,
        key=len,
        reverse=True
    )


    for name in sorted_names:

        if name in normalized:

            if name not in found:

                found.append(
                    name
                )


    return found


# ============================================================
# 提取爻位
# ============================================================

def extract_positions(query):

    normalized = normalize_text(
        query
    )

    found = []


    # 长的优先
    sorted_positions = sorted(
        YAO_POSITIONS,
        key=len,
        reverse=True
    )


    for position in sorted_positions:

        if position in normalized:

            if position not in found:

                found.append(
                    position
                )


    return found


# ============================================================
# 提取关键词
# ============================================================

def extract_keywords(query):

    query = query.strip()

    if not query:

        return []


    # --------------------------------------------------------
    # 中文连续片段
    # --------------------------------------------------------

    chinese_words = re.findall(
        r"[\u4e00-\u9fff]{2,}",
        query
    )


    # --------------------------------------------------------
    # 英文单词
    # --------------------------------------------------------

    english_words = re.findall(
        r"[A-Za-zÀ-ÿ]{2,}",
        query
    )


    raw_words = (
        chinese_words
        + english_words
    )


    keywords = []


    for word in raw_words:

        # -----------------------------------------------
        # 去掉《》
        # -----------------------------------------------

        word = (
            word
            .replace("《", "")
            .replace("》", "")
        )


        # -----------------------------------------------
        # 去掉提问词
        # -----------------------------------------------

        if word in STOP_WORDS:

            continue


        # -----------------------------------------------
        # 乾卦 → 乾
        # -----------------------------------------------

        if (
            word.endswith("卦")
            and len(word) > 1
        ):

            base = word[:-1]

            if base in HEXAGRAM_NAMES:

                word = base


        # -----------------------------------------------
        # 易经、尚书等保留
        # -----------------------------------------------

        if word:

            keywords.append(
                word
            )


    # ========================================================
    # 添加结构化关键词
    # ========================================================

    for item in (
        extract_books(query)
        + extract_hexagrams(query)
        + extract_positions(query)
    ):

        if item not in keywords:

            keywords.append(
                item
            )


    # ========================================================
    # 去重
    # ========================================================

    result = []

    for word in keywords:

        if word not in result:

            result.append(
                word
            )


    return result


# ============================================================
# 判断是不是有效文本
# ============================================================

def has_text(item):

    chinese = (
        item.get("chinese")
        or ""
    ).strip()

    french = (
        item.get("french")
        or ""
    ).strip()


    return bool(
        chinese
        or french
    )


# ============================================================
# 单条语料评分
# ============================================================

def score_item(
    item,
    keywords,
    books=None,
    hexagrams=None,
    positions=None
):

    books = books or []
    hexagrams = hexagrams or []
    positions = positions or []


    chinese = (
        item.get("chinese")
        or ""
    )

    french = (
        item.get("french")
        or ""
    )

    book = (
        item.get("book")
        or ""
    )

    chapter = (
        item.get("chapter")
        or ""
    )

    position = (
        item.get("position")
        or ""
    )

    item_type = (
        item.get("type")
        or ""
    )

    source = (
        item.get("source")
        or ""
    )


    score = 0


    # ========================================================
    # 1. 典籍精确匹配
    # ========================================================

    for target_book in books:

        if (
            target_book == source
            or target_book in book
        ):

            score += 40


    # ========================================================
    # 2. 卦名精确匹配
    # ========================================================

    for hexagram in hexagrams:

        # chapter = 乾
        if normalize_text(
            chapter
        ) == normalize_text(
            hexagram
        ):

            score += 50

        # book/chinese 中也命中
        elif (
            hexagram in chapter
            or hexagram in chinese
        ):

            score += 15


    # ========================================================
    # 3. 爻位精确匹配
    # ========================================================

    for target_position in positions:

        if (
            position
            == target_position
        ):

            score += 80

        elif (
            target_position
            in chinese
        ):

            score += 25


    # ========================================================
    # 4. 中文原文命中
    # ========================================================

    for keyword in keywords:

        if not keyword:

            continue


        if keyword in chinese:

            score += 10


    # ========================================================
    # 5. 法文命中
    # ========================================================

    french_lower = french.lower()

    for keyword in keywords:

        if not keyword:

            continue


        if (
            keyword.lower()
            in french_lower
        ):

            score += 5


    # ========================================================
    # 6. 章节名称命中
    # ========================================================

    for keyword in keywords:

        if not keyword:

            continue


        if keyword in chapter:

            score += 8


    # ========================================================
    # 7. 类型奖励
    # ========================================================

    #
    # 用户问“乾卦是什么”
    # 卦辞应该明显优先
    #

    if (
        hexagrams
        and not positions
        and item_type == "卦辞"
    ):

        score += 45


    # 如果用户明确问爻位
    # 爻辞优先

    if (
        positions
        and item_type == "爻辞"
    ):

        score += 30


    # ========================================================
    # 8. 有效文本奖励
    # ========================================================

    if has_text(item):

        score += 3

    else:

        # 空数据强烈降权
        score -= 30


    # ========================================================
    # 9. 易经结构化数据奖励
    # ========================================================

    if source == "易经":

        if (
            hexagrams
            or positions
        ):

            score += 10


    return score


# ============================================================
# 构造结果唯一键
# ============================================================

def result_key(item):

    return (
        item.get("source", ""),
        item.get("book", ""),
        item.get("chapter", ""),
        item.get("position", ""),
        item.get("type", ""),
        item.get("chinese", ""),
        item.get("french", "")
    )


# ============================================================
# 去除重复结果
# ============================================================

def deduplicate_results(results):

    seen = set()

    final = []


    for item in results:

        key = result_key(
            item
        )

        if key in seen:

            continue


        seen.add(
            key
        )

        final.append(
            item
        )


    return final


# ============================================================
# 判断是否是“卦名 + 爻位”
# ============================================================

def search_exact_hexagram_position(
    corpus,
    hexagram,
    position
):

    exact_results = []


    for item in corpus:

        if (
            item.get("source")
            != "易经"
        ):

            continue


        chapter = str(
            item.get(
                "chapter",
                ""
            )
        ).strip()


        item_position = str(
            item.get(
                "position",
                ""
            )
        ).strip()


        if (
            chapter == hexagram
            and item_position == position
        ):

            result = dict(
                item
            )

            result["score"] = 100

            exact_results.append(
                result
            )


    return exact_results


# ============================================================
# 搜索单个卦
# ============================================================

def search_hexagram(
    corpus,
    hexagram,
    top_k=8
):

    results = []


    for item in corpus:

        if (
            item.get("source")
            != "易经"
        ):

            continue


        chapter = str(
            item.get(
                "chapter",
                ""
            )
        ).strip()


        if chapter != hexagram:

            continue


        result = dict(
            item
        )


        # ====================================================
        # 卦辞最高优先级
        # ====================================================

        if (
            item.get("type")
            == "卦辞"
        ):

            result["score"] = 100


        # ====================================================
        # 特殊爻辞
        # ====================================================

        elif (
            item.get("type")
            == "特殊爻辞"
        ):

            result["score"] = 45


        # ====================================================
        # 普通爻辞
        # ====================================================

        else:

            result["score"] = 40


        results.append(
            result
        )


    # 卦辞优先
    results.sort(
        key=lambda x: (
            -x["score"],
            x.get(
                "position",
                ""
            )
        )
    )


    return results[:top_k]


# ============================================================
# 复合问题拆分
# ============================================================

def split_query_intents(query):

    """
    对类似：

    请介绍一下《易经》，并说明乾卦初九的含义

    进行简单结构化拆分。

    返回：

    [
        "易经",
        "乾卦初九"
    ]
    """

    intents = []


    books = extract_books(
        query
    )

    hexagrams = extract_hexagrams(
        query
    )

    positions = extract_positions(
        query
    )


    # ========================================================
    # 情况 1：
    # 卦名 + 爻位
    # ========================================================

    if (
        hexagrams
        and positions
    ):

        for hexagram in hexagrams:

            for position in positions:

                intents.append(
                    f"{hexagram}卦 {position}"
                )


    # ========================================================
    # 情况 2：
    # 单独典籍
    # ========================================================

    if books:

        for book in books:

            if book not in [
                item.replace(
                    "卦 ",
                    ""
                ).replace(
                    "卦",
                    ""
                )
                for item in intents
            ]:

                intents.append(
                    book
                )


    # ========================================================
    # 情况 3：
    # 单独卦名
    # ========================================================

    if (
        hexagrams
        and not positions
    ):

        for hexagram in hexagrams:

            intent = (
                f"{hexagram}卦"
            )

            if intent not in intents:

                intents.append(
                    intent
                )


    # ========================================================
    # 如果没有结构化意图
    # ========================================================

    if not intents:

        intents.append(
            query
        )


    # 去重
    result = []

    for intent in intents:

        if intent not in result:

            result.append(
                intent
            )


    return result


# ============================================================
# 普通关键词检索
# ============================================================

def search_by_keywords(
    corpus,
    query,
    top_k=8
):

    keywords = extract_keywords(
        query
    )

    books = extract_books(
        query
    )

    hexagrams = extract_hexagrams(
        query
    )

    positions = extract_positions(
        query
    )


    if not keywords:

        return []


    scored_results = []


    for item in corpus:

        score = score_item(
            item,
            keywords,
            books=books,
            hexagrams=hexagrams,
            positions=positions
        )


        if score <= 0:

            continue


        result = dict(
            item
        )

        result["score"] = score

        scored_results.append(
            result
        )


    scored_results.sort(
        key=lambda x: (
            -x["score"],
            x.get(
                "source",
                ""
            ),
            x.get(
                "chapter",
                ""
            )
        )
    )


    return scored_results[:top_k]


# ============================================================
# 主检索函数
# ============================================================

def search_corpus(
    query,
    top_k=8
):

    corpus = load_corpus()


    query = (
        query
        or ""
    ).strip()


    if not query:

        return []


    # ========================================================
    # 分析问题
    # ========================================================

    books = extract_books(
        query
    )

    hexagrams = extract_hexagrams(
        query
    )

    positions = extract_positions(
        query
    )

    keywords = extract_keywords(
        query
    )


    # ========================================================
    # 输出调试信息
    # ========================================================

    print()
    print(
        "RAG 检索分析："
    )

    print(
        f"  典籍：{books}"
    )

    print(
        f"  卦名：{hexagrams}"
    )

    print(
        f"  爻位：{positions}"
    )

    print(
        f"  关键词：{keywords}"
    )

    print(
        f"  原始语料总数：{len(corpus)}"
    )


    # ========================================================
    # 第一优先级：
    # 卦名 + 爻位精确检索
    # ========================================================

    if (
        hexagrams
        and positions
    ):

        exact_results = []


        for hexagram in hexagrams:

            for position in positions:

                exact = (
                    search_exact_hexagram_position(
                        corpus,
                        hexagram,
                        position
                    )
                )

                exact_results.extend(
                    exact
                )


        exact_results = (
            deduplicate_results(
                exact_results
            )
        )


        if exact_results:

            print(
                "  ✓ 使用卦名 + 爻位精确检索"
            )

            return exact_results[
                :top_k
            ]


    # ========================================================
    # 第二优先级：
    # 单独查询某一卦
    # ========================================================

    if (
        hexagrams
        and not positions
    ):

        hexagram_results = []


        for hexagram in hexagrams:

            results = search_hexagram(
                corpus,
                hexagram,
                top_k=top_k
            )

            hexagram_results.extend(
                results
            )


        hexagram_results = (
            deduplicate_results(
                hexagram_results
            )
        )


        if hexagram_results:

            print(
                "  ✓ 使用卦名结构化检索"
            )

            return hexagram_results[
                :top_k
            ]


    # ========================================================
    # 第三优先级：
    # 普通关键词检索
    # ========================================================

    results = search_by_keywords(
        corpus,
        query,
        top_k=top_k * 2
    )


    results = deduplicate_results(
        results
    )


    # ========================================================
    # 对空文本结果进一步过滤
    # ========================================================

    useful_results = []

    empty_results = []


    for item in results:

        if has_text(item):

            useful_results.append(
                item
            )

        else:

            empty_results.append(
                item
            )


    # ========================================================
    # 优先返回有实际文本的结果
    # ========================================================

    final_results = (
        useful_results
        if useful_results
        else empty_results
    )


    # ========================================================
    # 最终排序
    # ========================================================

    final_results.sort(
        key=lambda x: (
            -x.get(
                "score",
                0
            )
        )
    )


    print(
        f"  ✓ 普通关键词检索返回："
        f"{len(final_results[:top_k])} 条"
    )


    return final_results[
        :top_k
    ]


# ============================================================
# 本地测试
# ============================================================

if __name__ == "__main__":

    print(
        "=" * 60
    )

    print(
        "五经古典语料库 RAG 检索测试"
    )

    print(
        "=" * 60
    )

    print()

    print(
        "正在加载五经语料库……"
    )


    corpus = load_corpus()


    print(
        f"✓ 共加载 {len(corpus)} 条语料"
    )

    print()


    while True:

        question = input(
            "请输入检索问题（输入 q 退出）："
        ).strip()


        if question.lower() == "q":

            break


        if not question:

            continue


        results = search_corpus(
            question,
            top_k=10
        )


        print()

        print(
            "=" * 60
        )

        print(
            f"检索结果：{len(results)} 条"
        )

        print(
            "=" * 60
        )


        for i, item in enumerate(
            results,
            start=1
        ):

            print()

            print(
                f"【结果 {i}】"
            )

            print(
                f"典籍："
                f"{item.get('book', '')}"
            )

            print(
                f"章节："
                f"{item.get('chapter', '')}"
            )


            if item.get(
                "position"
            ):

                print(
                    f"位置："
                    f"{item.get('position')}"
                )


            if item.get(
                "type"
            ):

                print(
                    f"类型："
                    f"{item.get('type')}"
                )


            print(
                f"来源："
                f"{item.get('source', '')}"
            )


            print(
                f"相关度："
                f"{item.get('score', 0)}"
            )


            print(
                f"中文："
                f"{item.get('chinese', '')}"
            )


            print(
                f"法文："
                f"{item.get('french', '')}"
            )


            print(
                "-" * 60
            )

        print()