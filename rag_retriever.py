import json
import re
from pathlib import Path
from typing import List, Dict, Any


# ============================================================
# 五经古典语料库
# RAG 检索器
#
# 当前版本：
# 1. 使用 normalized_corpus.json
# 2. 支持五经识别
# 3. 支持《易经》卦名识别
# 4. 支持《易经》爻位识别
# 5. 支持《春秋》公、卷、年份识别
# 6. 结构化条件采用“硬过滤”
# 7. 过滤完成后再进行关键词相关度排序
# ============================================================


BASE_DIR = Path(__file__).resolve().parent
CORPUS_FILE = BASE_DIR / "normalized_corpus.json"


# ============================================================
# 1. 读取统一语料库
# ============================================================

def load_corpus() -> List[Dict[str, Any]]:
    """读取 normalized_corpus.json"""

    if not CORPUS_FILE.exists():
        raise FileNotFoundError(
            f"找不到统一语料库：{CORPUS_FILE}"
        )

    with open(CORPUS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(
            "normalized_corpus.json 顶层结构不是 list"
        )

    # 加载自定义扩充语料
    custom_file = BASE_DIR / "custom_corpus.json"
    if custom_file.exists():
        with open(custom_file, "r", encoding="utf-8") as f:
            custom_data = json.load(f)

        if not isinstance(custom_data, list):
            raise ValueError(
                "custom_corpus.json 顶层结构不是 list"
            )

        data.extend(custom_data)

    return data


# ============================================================
# 2. 判断记录是否具有可检索内容
# ============================================================

def is_valid_record(record: Dict[str, Any]) -> bool:
    """
    判断一条记录是否具有有效的中文或法文内容。

    中文、法文至少有一个有效，才进入检索。
    """

    chinese = str(
        record.get("chinese", "") or ""
    ).strip()

    french = str(
        record.get("french", "") or ""
    ).strip()

    invalid_values = {
        "",
        "nan",
        "none",
        "null",
    }

    chinese_valid = (
        chinese.lower() not in invalid_values
    )

    french_valid = (
        french.lower() not in invalid_values
    )

    return chinese_valid or french_valid


# ============================================================
# 3. 典籍识别
# ============================================================

BOOK_ALIASES = {
    "易经": "易经",
    "周易": "易经",
    "易": "易经",

    "尚书": "尚书",
    "书经": "尚书",
    "书": "尚书",

    "诗经": "诗经",
    "诗": "诗经",

    "礼记": "礼记",
    "礼": "礼记",

    "春秋": "春秋",
}


def detect_book(query: str) -> List[str]:
    """识别用户问题中提到的典籍"""

    books = []

    # 长关键词优先
    aliases = sorted(
        BOOK_ALIASES.keys(),
        key=len,
        reverse=True
    )

    for alias in aliases:

        if alias in query:

            book = BOOK_ALIASES[alias]

            if book not in books:
                books.append(book)

    return books


# ============================================================
# 4. 《易经》卦名识别
# ============================================================

HEXAGRAM_NAMES = [
    "乾", "坤", "屯", "蒙", "需", "讼", "师", "比",
    "小畜", "履", "泰", "否", "同人", "大有", "谦", "豫",
    "随", "蛊", "临", "观", "噬嗑", "贲", "剥", "复",
    "无妄", "大畜", "颐", "大过", "坎", "离", "咸", "恒",
    "遁", "大壮", "晋", "明夷", "家人", "睽", "蹇", "解",
    "损", "益", "夬", "姤", "萃", "升", "困", "井",
    "革", "鼎", "震", "艮", "渐", "归妹", "丰", "旅",
    "巽", "兑", "涣", "节", "中孚", "小过", "既济", "未济"
]


def detect_hexagram(query: str) -> List[str]:
    """识别《易经》卦名"""

    result = []

    for name in sorted(
        HEXAGRAM_NAMES,
        key=len,
        reverse=True
    ):

        if name in query:

            if name not in result:
                result.append(name)

    return result


# ============================================================
# 5. 《易经》爻位识别
# ============================================================

YAO_POSITIONS = [
    "初九",
    "九二",
    "九三",
    "九四",
    "九五",
    "上九",

    "初六",
    "六二",
    "六三",
    "六四",
    "六五",
    "上六",

    "用九",
    "用六",
]


def detect_yao_position(query: str) -> List[str]:
    """识别《易经》爻位"""

    result = []

    for position in YAO_POSITIONS:

        if position in query:

            if position not in result:
                result.append(position)

    return result


# ============================================================
# 6. 《春秋》结构化信息识别
# ============================================================

DUKES = [
    "隐公",
    "桓公",
    "庄公",
    "闵公",
    "僖公",
    "文公",
    "宣公",
    "成公",
    "襄公",
    "昭公",
    "定公",
    "哀公",
]


def detect_duke(query: str) -> List[str]:
    """识别《春秋》中的公"""

    result = []

    for duke in DUKES:

        if duke in query:

            if duke not in result:
                result.append(duke)

    return result


# ============================================================
# 7. 《春秋》卷号识别
# ============================================================

def detect_juan(query: str) -> List[str]:
    """识别《春秋》卷号"""

    result = []

    matches = re.findall(
        r"卷[一二三四五六七八九十百]+",
        query
    )

    for item in matches:

        if item not in result:
            result.append(item)

    return result


# ============================================================
# 8. 《春秋》年份识别
# ============================================================

def detect_year(query: str) -> List[str]:
    """
    识别《春秋》年份。

    例如：
    僖公二十八年
    襄公二十一年
    昭公三年
    """

    result = []

    pattern = (
        r"(?:"
        r"隐公|桓公|庄公|闵公|僖公|文公|宣公|"
        r"成公|襄公|昭公|定公|哀公"
        r")"
        r"[一二三四五六七八九十百千]+年"
    )

    matches = re.findall(
        pattern,
        query
    )

    for item in matches:

        if item not in result:
            result.append(item)

    return result


# ============================================================
# 9. 查询关键词提取
# ============================================================

STOP_WORDS = {
    "请",
    "请问",
    "一下",
    "介绍",
    "说明",
    "告诉",
    "什么",
    "是什么",
    "怎么",
    "如何",
    "为什么",
    "意思",
    "含义",
    "有关",
    "关于",
    "的",
    "是",
    "吗",
    "呢",
    "啊",
    "和",
    "与",
    "并",
    "及",
}


def extract_keywords(query: str) -> List[str]:
    """
    简单关键词提取。

    当前版本主要采用：
    1. 原始问题
    2. 去掉常见停用词后的词
    3. 中文连续片段
    """

    keywords = []

    cleaned = query.strip()

    if cleaned:
        keywords.append(cleaned)

    chinese_parts = re.findall(
        r"[\u4e00-\u9fff]+",
        cleaned
    )

    for part in chinese_parts:

        if len(part) > 2:

            temp = part

            for word in STOP_WORDS:
                temp = temp.replace(
                    word,
                    ""
                )

            if (
                temp
                and temp not in keywords
            ):
                keywords.append(temp)

        if 1 <= len(part) <= 4:

            if (
                part not in STOP_WORDS
                and part not in keywords
            ):
                keywords.append(part)

    return keywords


# ============================================================
# 10. 结构化硬过滤
# ============================================================

def filter_structured_records(
    records: List[Dict[str, Any]],
    books: List[str],
    hexagrams: List[str],
    positions: List[str],
    dukes: List[str],
    juans: List[str],
    years: List[str],
) -> List[Dict[str, Any]]:
    """
    根据用户问题中的结构化信息进行硬过滤。

    重要原则：

    如果用户明确指定某个结构化条件，
    那么记录必须满足该条件才能继续进入评分。

    例如：

    乾卦 + 初九

    必须同时满足：

        chapter == 乾
        position == 初九

    而不是只给“初九”加分。

    这可以避免：
        乾卦初九
    被其他卦的初九污染。
    """

    filtered = []

    for record in records:

        # ----------------------------------------------------
        # 典籍硬过滤
        # ----------------------------------------------------

        if books:

            book = str(
                record.get("book", "") or ""
            ).strip()

            if book not in books:
                continue

        # ----------------------------------------------------
        # 《易经》卦名硬过滤
        # ----------------------------------------------------

        if hexagrams:

            chapter = str(
                record.get("chapter", "") or ""
            ).strip()

            # 必须属于指定卦名
            if chapter not in hexagrams:
                continue

        # ----------------------------------------------------
        # 《易经》爻位硬过滤
        # ----------------------------------------------------

        if positions:

            position = str(
                record.get("position", "") or ""
            ).strip()

            if position not in positions:
                continue

        # ----------------------------------------------------
        # 《春秋》公硬过滤
        # ----------------------------------------------------

        if dukes:

            duke_cn = str(
                record.get("duke_cn", "") or ""
            ).strip()

            if duke_cn not in dukes:
                continue

        # ----------------------------------------------------
        # 《春秋》卷号硬过滤
        # ----------------------------------------------------

        if juans:

            juan = str(
                record.get("juan", "") or ""
            ).strip()

            if juan not in juans:
                continue

        # ----------------------------------------------------
        # 《春秋》年份硬过滤
        # ----------------------------------------------------

        if years:

            year_cn = str(
                record.get("year_cn", "") or ""
            ).strip()

            if year_cn not in years:
                continue

        # ----------------------------------------------------
        # 所有结构化条件都通过
        # ----------------------------------------------------

        filtered.append(record)

    return filtered


# ============================================================
# 11. 单条记录评分
# ============================================================

def calculate_score(
    record: Dict[str, Any],
    query: str,
    books: List[str],
    hexagrams: List[str],
    positions: List[str],
    dukes: List[str],
    juans: List[str],
    years: List[str],
    keywords: List[str],
) -> int:

    score = 0

    book = str(
        record.get("book", "") or ""
    )

    chapter = str(
        record.get("chapter", "") or ""
    )

    position = str(
        record.get("position", "") or ""
    )

    chinese = str(
        record.get("chinese", "") or ""
    )

    french = str(
        record.get("french", "") or ""
    )

    # --------------------------------------------------------
    # 典籍匹配
    # --------------------------------------------------------

    if books and book in books:
        score += 30

    # --------------------------------------------------------
    # 《易经》卦名匹配
    # --------------------------------------------------------

    if hexagrams:

        if chapter in hexagrams:
            score += 50

    # --------------------------------------------------------
    # 爻位匹配
    # --------------------------------------------------------

    if positions:

        if position in positions:
            score += 80

    # --------------------------------------------------------
    # 《春秋》公匹配
    # --------------------------------------------------------

    if dukes:

        duke_cn = str(
            record.get("duke_cn", "") or ""
        )

        if duke_cn in dukes:
            score += 50

    # --------------------------------------------------------
    # 《春秋》卷匹配
    # --------------------------------------------------------

    if juans:

        juan = str(
            record.get("juan", "") or ""
        )

        if juan in juans:
            score += 40

    # --------------------------------------------------------
    # 《春秋》年份匹配
    # --------------------------------------------------------

    if years:

        year_cn = str(
            record.get("year_cn", "") or ""
        )

        if year_cn in years:
            score += 80

    # --------------------------------------------------------
    # 原始问题匹配
    # --------------------------------------------------------

    if query:

        if query in chinese:
            score += 30

        if query in french:
            score += 10

    # --------------------------------------------------------
    # 关键词匹配
    # --------------------------------------------------------

    for keyword in keywords:

        if not keyword:
            continue

        if keyword in chinese:
            score += 15

        if keyword in chapter:
            score += 10

        if keyword in position:
            score += 15

        if keyword in book:
            score += 10

    return score


# ============================================================
# 12. RAG 检索主函数
# ============================================================

def retrieve(
    query: str,
    top_k: int = 8
) -> Dict[str, Any]:

    corpus = load_corpus()

    # --------------------------------------------------------
    # 结构化信息识别
    # --------------------------------------------------------

    books = detect_book(query)

    hexagrams = detect_hexagram(query)

    positions = detect_yao_position(query)

    dukes = detect_duke(query)

    juans = detect_juan(query)

    years = detect_year(query)

    keywords = extract_keywords(query)

    # --------------------------------------------------------
    # 有效数据过滤
    # --------------------------------------------------------

    valid_records = [
        record
        for record in corpus
        if is_valid_record(record)
    ]

    # --------------------------------------------------------
    # ★ 新增：结构化硬过滤
    # --------------------------------------------------------

    filtered_records = filter_structured_records(
        records=valid_records,
        books=books,
        hexagrams=hexagrams,
        positions=positions,
        dukes=dukes,
        juans=juans,
        years=years,
    )

    # --------------------------------------------------------
    # 评分
    # --------------------------------------------------------

    scored_results = []

    for record in filtered_records:

        score = calculate_score(
            record=record,
            query=query,
            books=books,
            hexagrams=hexagrams,
            positions=positions,
            dukes=dukes,
            juans=juans,
            years=years,
            keywords=keywords,
        )

        if score > 0:

            scored_results.append(
                {
                    "score": score,
                    "record": record,
                }
            )

    # --------------------------------------------------------
    # 排序
    # --------------------------------------------------------

    scored_results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    results = scored_results[:top_k]

    # --------------------------------------------------------
    # 返回
    # --------------------------------------------------------

    return {
        "query": query,

        "analysis": {

            "books": books,

            "hexagrams": hexagrams,

            "positions": positions,

            "dukes": dukes,

            "juans": juans,

            "years": years,

            "keywords": keywords,

            "total_records": len(corpus),

            "valid_records": len(valid_records),

            "filtered_records": len(filtered_records),

            "excluded_records": (
                len(corpus)
                - len(valid_records)
            ),

            "structured_filtered_records": (
                len(valid_records)
                - len(filtered_records)
            ),
        },

        "results": results,
    }


# ============================================================
# 13. 结果显示
# ============================================================

def print_results(
    result: Dict[str, Any]
):

    query = result["query"]

    analysis = result["analysis"]

    results = result["results"]

    print()

    print("=" * 60)

    print("RAG 检索分析")

    print("=" * 60)

    print(
        f"问题：{query}"
    )

    print(
        f"典籍：{analysis['books']}"
    )

    print(
        f"卦名：{analysis['hexagrams']}"
    )

    print(
        f"爻位：{analysis['positions']}"
    )

    print(
        f"公：{analysis['dukes']}"
    )

    print(
        f"卷：{analysis['juans']}"
    )

    print(
        f"年份：{analysis['years']}"
    )

    print(
        f"关键词：{analysis['keywords']}"
    )

    print(
        f"原始语料总数："
        f"{analysis['total_records']}"
    )

    print(
        f"有效检索语料："
        f"{analysis['valid_records']}"
    )

    print(
        f"结构化过滤后："
        f"{analysis['filtered_records']}"
    )

    print(
        f"因结构化条件排除："
        f"{analysis['structured_filtered_records']}"
    )

    print(
        f"排除无效记录："
        f"{analysis['excluded_records']}"
    )

    print()

    print("=" * 60)

    print(
        f"检索结果：{len(results)} 条"
    )

    print("=" * 60)

    if not results:

        print(
            "没有找到相关语料。"
        )

        return

    for index, item in enumerate(
        results,
        start=1
    ):

        record = item["record"]

        score = item["score"]

        print()

        print(
            f"【结果 {index}】"
        )

        print(
            f"相关度：{score}"
        )

        print(
            f"ID：{record.get('id', '')}"
        )

        print(
            f"典籍：{record.get('book', '')}"
        )

        print(
            f"章节：{record.get('chapter', '')}"
        )

        if record.get("juan"):

            print(
                f"卷：{record.get('juan')}"
            )

        if record.get("duke_cn"):

            print(
                f"公：{record.get('duke_cn')}"
            )

        if record.get("year_cn"):

            print(
                f"年份：{record.get('year_cn')}"
            )

        if record.get("position"):

            print(
                f"位置：{record.get('position')}"
            )

        print(
            f"类型：{record.get('type', '')}"
        )

        if record.get("hexagram_no"):

            print(
                f"卦号：{record.get('hexagram_no')}"
            )

        print(
            f"中文：{record.get('chinese', '')}"
        )

        print(
            f"法文：{record.get('french', '')}"
        )

        print(
            f"来源：{record.get('source', '')}"
        )

        print(
            "-" * 60
        )


# ============================================================
# 14. 命令行测试
# ============================================================

def main():

    print("=" * 60)

    print(
        "五经古典语料库 - RAG 检索系统"
    )

    print("=" * 60)

    print(
        f"语料库：{CORPUS_FILE}"
    )

    try:

        corpus = load_corpus()

        print(
            f"✓ 语料库读取成功："
            f"{len(corpus)} 条"
        )

    except Exception as e:

        print(
            f"✗ 读取语料库失败：{e}"
        )

        return

    print()

    print(
        "系统已经启动。"
    )

    print(
        "输入问题进行检索。"
    )

    print(
        "输入 q 退出。"
    )

    print()

    while True:

        try:

            query = input(
                "请输入检索问题："
            ).strip()

        except (
            KeyboardInterrupt,
            EOFError
        ):

            print()

            print(
                "退出系统。"
            )

            break

        if not query:
            continue

        if query.lower() == "q":

            print(
                "退出系统。"
            )

            break

        try:

            result = retrieve(
                query=query,
                top_k=8
            )

            print_results(
                result
            )

        except Exception as e:

            print()

            print(
                "✗ 检索过程中出现错误："
            )

            print(e)


# ============================================================
# 程序入口
# ============================================================

if __name__ == "__main__":
    main()