import json
import collections
import os


# ============================================================
# 五经古典语料库 - normalized_corpus.json 数据质量最终检查
# ============================================================

FILE_PATH = "normalized_corpus.json"


def print_line():
    print("-" * 70)


def main():

    print("=" * 70)
    print("五经古典语料库 - normalized_corpus.json 数据质量检查")
    print("=" * 70)

    # --------------------------------------------------------
    # 1. 检查文件
    # --------------------------------------------------------
    print("\n【1】检查 JSON 文件")

    if not os.path.exists(FILE_PATH):
        print(f"✗ 找不到文件：{FILE_PATH}")
        print("请确认 normalized_corpus.json 位于当前目录。")
        return

    try:
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        print("✓ JSON 文件读取成功")

    except Exception as e:
        print("✗ JSON 文件读取失败")
        print("错误：", e)
        return

    # --------------------------------------------------------
    # 2. 基本信息
    # --------------------------------------------------------
    print("\n【2】基本信息")

    print("总记录数：", len(data))

    if isinstance(data, list):
        print("顶层结构：list ✓")
    else:
        print("顶层结构：", type(data).__name__, "✗")
        print("错误：标准化语料库应该是 list 结构。")
        return

    # --------------------------------------------------------
    # 3. 典籍统计
    # --------------------------------------------------------
    print("\n【3】典籍统计")

    book_counter = collections.Counter(
        str(item.get("book", "")).strip()
        for item in data
    )

    for book, count in book_counter.items():
        if book:
            print(f"  {book}: {count} 条")

    empty_book = book_counter.get("", 0)

    if empty_book == 0:
        print("  ✓ book 字段全部存在")
    else:
        print(f"  ✗ book 为空：{empty_book} 条")

    # --------------------------------------------------------
    # 4. 中文与法文完整性
    # --------------------------------------------------------
    print("\n【4】中文与法文完整性")

    empty_chinese = []
    empty_french = []

    for index, item in enumerate(data):

        chinese = str(item.get("chinese", "")).strip()
        french = str(item.get("french", "")).strip()

        # 统一识别常见空值
        chinese_empty = (
            chinese == ""
            or chinese.lower() == "nan"
            or chinese.lower() == "none"
            or chinese.lower() == "null"
        )

        french_empty = (
            french == ""
            or french.lower() == "nan"
            or french.lower() == "none"
            or french.lower() == "null"
        )

        if chinese_empty:
            empty_chinese.append((index, item))

        if french_empty:
            empty_french.append((index, item))

    print(f"中文为空：{len(empty_chinese)} 条")
    print(f"法文为空：{len(empty_french)} 条")

    # --------------------------------------------------------
    # 5. 输出中文为空的全部记录
    # --------------------------------------------------------
    print("\n【5】中文为空的记录")

    if len(empty_chinese) == 0:
        print("✓ 没有中文为空的记录")
    else:

        for index, item in empty_chinese:
            print_line()
            print(f"原始索引：{index}")
            print("ID：", item.get("id", ""))
            print("典籍：", item.get("book", ""))
            print("章节：", item.get("chapter", ""))
            print("位置：", item.get("position", ""))
            print("类型：", item.get("type", ""))
            print("中文：", repr(item.get("chinese", "")))
            print("法文：", repr(item.get("french", "")))
            print("来源：", item.get("source", ""))

    # --------------------------------------------------------
    # 6. 输出法文为空的全部记录
    # --------------------------------------------------------
    print("\n【6】法文为空的记录")

    if len(empty_french) == 0:
        print("✓ 没有法文为空的记录")
    else:

        for index, item in empty_french:
            print_line()
            print(f"原始索引：{index}")
            print("ID：", item.get("id", ""))
            print("典籍：", item.get("book", ""))
            print("章节：", item.get("chapter", ""))
            print("位置：", item.get("position", ""))
            print("类型：", item.get("type", ""))
            print("中文：", repr(item.get("chinese", "")))
            print("法文：", repr(item.get("french", "")))
            print("来源：", item.get("source", ""))

    # --------------------------------------------------------
    # 7. 检查特殊脏数据
    # --------------------------------------------------------
    print("\n【7】检查特殊脏数据")

    nan_records = []
    none_records = []

    for index, item in enumerate(data):

        for field in ["book", "chapter", "position", "type", "chinese", "french", "source"]:

            value = item.get(field)

            if isinstance(value, str):

                if value.strip().lower() == "nan":
                    nan_records.append((index, field, item))

                if value.strip().lower() == "none":
                    none_records.append((index, field, item))

    print(f"发现字符串 'nan'：{len(nan_records)} 处")
    print(f"发现字符串 'none'：{len(none_records)} 处")

    if nan_records:
        print("\n包含 'nan' 的位置：")

        for index, field, item in nan_records[:30]:
            print(
                f"  索引 {index} | 字段 {field} | "
                f"典籍 {item.get('book', '')} | "
                f"ID {item.get('id', '')}"
            )

        if len(nan_records) > 30:
            print(f"  ……其余 {len(nan_records) - 30} 处未显示")

    # --------------------------------------------------------
    # 8. ID 检查
    # --------------------------------------------------------
    print("\n【8】ID 检查")

    ids = []
    missing_id = []

    for index, item in enumerate(data):

        record_id = item.get("id")

        if record_id is None or str(record_id).strip() == "":
            missing_id.append((index, item))
        else:
            ids.append(str(record_id))

    id_counter = collections.Counter(ids)

    duplicate_ids = {
        record_id: count
        for record_id, count in id_counter.items()
        if count > 1
    }

    print("记录总数：", len(data))
    print("存在 ID：", len(ids))
    print("唯一 ID 数：", len(id_counter))
    print("缺少 ID：", len(missing_id))
    print("重复 ID：", len(duplicate_ids))

    if missing_id:
        print("\n缺少 ID 的记录：")

        for index, item in missing_id[:20]:
            print(
                f"  索引 {index} | "
                f"典籍 {item.get('book', '')} | "
                f"章节 {item.get('chapter', '')}"
            )

        if len(missing_id) > 20:
            print(f"  ……其余 {len(missing_id) - 20} 条未显示")

    if duplicate_ids:
        print("\n重复 ID：")

        for record_id, count in duplicate_ids.items():
            print(f"  {record_id} → {count} 次")

    # --------------------------------------------------------
    # 9. 完全重复记录
    # --------------------------------------------------------
    print("\n【9】完全重复记录检查")

    record_strings = []

    for item in data:
        record_strings.append(
            json.dumps(
                item,
                ensure_ascii=False,
                sort_keys=True
            )
        )

    record_counter = collections.Counter(record_strings)

    duplicate_records = {
        record: count
        for record, count in record_counter.items()
        if count > 1
    }

    print("完全重复记录组数：", len(duplicate_records))

    if duplicate_records:
        print("发现完全重复记录：")

        shown = 0

        for record, count in duplicate_records.items():

            print_line()
            print(f"重复次数：{count}")
            print(json.loads(record))

            shown += 1

            if shown >= 20:
                print("……仅显示前 20 组")
                break

    else:
        print("✓ 没有完全重复记录")

    # --------------------------------------------------------
    # 10. 检查五部经典数量
    # --------------------------------------------------------
    print("\n【10】五经数据数量检查")

    expected_books = {
        "尚书": 50,
        "诗经": 49,
        "礼记": 323,
        "春秋": 1826,
        "易经": 451,
    }

    all_book_count_correct = True

    for book, expected in expected_books.items():

        actual = book_counter.get(book, 0)

        if actual == expected:
            print(f"  ✓ {book}：{actual} 条")
        else:
            print(
                f"  ✗ {book}：实际 {actual} 条，"
                f"预期 {expected} 条"
            )
            all_book_count_correct = False

    # --------------------------------------------------------
    # 11. 《易经》专项检查
    # --------------------------------------------------------
    print("\n【11】《易经》专项检查")

    yijing_data = [
        item for item in data
        if str(item.get("book", "")).strip() == "易经"
    ]

    print("《易经》记录：", len(yijing_data), "条")

    hexagrams = set()

    for item in yijing_data:

        hexagram = str(item.get("chapter", "")).strip()

        if hexagram:
            hexagrams.add(hexagram)

    print("《易经》卦名数量：", len(hexagrams))

    if len(yijing_data) == 451:
        print("✓ 《易经》记录数量正确")
    else:
        print("✗ 《易经》记录数量异常")

    if len(hexagrams) == 64:
        print("✓ 《易经》包含 64 卦")
    else:
        print("✗ 《易经》卦数异常")

    # --------------------------------------------------------
    # 12. 《春秋》专项检查
    # --------------------------------------------------------
    print("\n【12】《春秋》专项检查")

    chunqiu_data = [
        item for item in data
        if str(item.get("book", "")).strip() == "春秋"
    ]

    print("《春秋》记录：", len(chunqiu_data), "条")

    if len(chunqiu_data) == 1826:
        print("✓ 《春秋》记录数量正确")
    else:
        print("✗ 《春秋》记录数量异常")

    # --------------------------------------------------------
    # 13. 检查来源字段
    # --------------------------------------------------------
    print("\n【13】来源字段检查")

    empty_source = []

    for index, item in enumerate(data):

        source = str(item.get("source", "")).strip()

        if (
            source == ""
            or source.lower() == "nan"
            or source.lower() == "none"
        ):
            empty_source.append((index, item))

    print("来源为空：", len(empty_source), "条")

    if empty_source:

        print("\n前 20 条来源为空的记录：")

        for index, item in empty_source[:20]:
            print(
                f"  索引 {index} | "
                f"ID {item.get('id', '')} | "
                f"典籍 {item.get('book', '')} | "
                f"章节 {item.get('chapter', '')}"
            )

    else:
        print("✓ 所有记录都有来源")

    # --------------------------------------------------------
    # 14. 字段结构检查
    # --------------------------------------------------------
    print("\n【14】字段结构检查")

    field_structures = collections.Counter()

    for item in data:

        fields = tuple(sorted(item.keys()))
        field_structures[fields] += 1

    print("发现", len(field_structures), "种字段结构")

    for number, (fields, count) in enumerate(
        field_structures.items(),
        start=1
    ):

        print(f"\n结构 {number}：{count} 条")
        print("字段：", list(fields))

    # --------------------------------------------------------
    # 15. 最终判断
    # --------------------------------------------------------
    print("\n" + "=" * 70)
    print("最终检查结果")
    print("=" * 70)

    problems = []

    if len(data) != 2699:
        problems.append(
            f"总记录数异常：{len(data)}（预期 2699）"
        )

    if empty_book:
        problems.append(
            f"存在 {empty_book} 条 book 为空的记录"
        )

    if len(empty_chinese):
        problems.append(
            f"存在 {len(empty_chinese)} 条中文为空的记录"
        )

    if len(empty_french):
        problems.append(
            f"存在 {len(empty_french)} 条法文为空的记录"
        )

    if missing_id:
        problems.append(
            f"存在 {len(missing_id)} 条记录缺少 ID"
        )

    if duplicate_ids:
        problems.append(
            f"存在 {len(duplicate_ids)} 个重复 ID"
        )

    if duplicate_records:
        problems.append(
            f"存在 {len(duplicate_records)} 组完全重复记录"
        )

    if not all_book_count_correct:
        problems.append("五部经典记录数量与预期不一致")

    if len(yijing_data) != 451:
        problems.append("《易经》记录数量异常")

    if len(hexagrams) != 64:
        problems.append("《易经》卦数不是 64")

    if len(chunqiu_data) != 1826:
        problems.append("《春秋》记录数量异常")

    if empty_source:
        problems.append(
            f"存在 {len(empty_source)} 条来源为空的记录"
        )

    if problems:

        print("⚠ 当前仍发现以下问题：")

        for i, problem in enumerate(problems, start=1):
            print(f"{i}. {problem}")

        print("\n这些问题暂时不要自己修改数据。")
        print("把完整运行结果发给我，我们逐项判断哪些是真问题。")

    else:

        print("🎉 所有检查均通过！")
        print()
        print("✓ JSON 结构正常")
        print("✓ 总记录数正确")
        print("✓ 五部经典数量正确")
        print("✓ book 字段完整")
        print("✓ 中文字段完整")
        print("✓ 法文字段完整")
        print("✓ ID 全部唯一")
        print("✓ 没有完全重复记录")
        print("✓ 《易经》64 卦完整")
        print("✓ 《春秋》1826 条完整")
        print()
        print(">>> normalized_corpus.json 已达到 RAG 接入前的数据验收标准。")

    print("\n" + "=" * 70)
    print("检查完成")
    print("=" * 70)


if __name__ == "__main__":
    main()