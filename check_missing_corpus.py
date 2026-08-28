import json
import os


# ============================================================
# 五经古典语料库 - 《春秋》缺失数据源头检查
# ============================================================

NORMALIZED_FILE = "normalized_corpus.json"
CHUNQIU_FILE = "chunqiu_corpus.json (JSON结构化数据).json"


def is_empty(value):
    """
    判断字段是否为空。
    同时识别：
    空字符串、None、nan、none、null
    """
    if value is None:
        return True

    text = str(value).strip()

    if text == "":
        return True

    if text.lower() in ["nan", "none", "null"]:
        return True

    return False


def print_record(title, record):
    print("-" * 70)
    print(title)

    print("ID：", record.get("id", ""))
    print("典籍：", record.get("book", ""))
    print("卷：", record.get("juan", ""))
    print("卷法文：", record.get("juan_fr", ""))
    print("公：", record.get("duke_cn", ""))
    print("公法文：", record.get("duke_fr", ""))
    print("年份：", record.get("year_cn", ""))
    print("年份法文：", record.get("year_fr", ""))
    print("公元年份：", record.get("year_bc", ""))
    print("卷内序号：", record.get("seq_in_juan", ""))

    print("中文：", repr(record.get("chinese", "")))
    print("法文：", repr(record.get("french", "")))


def main():

    print("=" * 70)
    print("五经古典语料库 - 《春秋》缺失数据源头检查")
    print("=" * 70)

    # ========================================================
    # 1. 检查文件
    # ========================================================

    print("\n【1】检查文件")

    if not os.path.exists(NORMALIZED_FILE):
        print(f"✗ 找不到：{NORMALIZED_FILE}")
        return

    print(f"✓ 找到：{NORMALIZED_FILE}")

    if not os.path.exists(CHUNQIU_FILE):
        print(f"✗ 找不到：{CHUNQIU_FILE}")
        print()
        print("请确认文件名是否为：")
        print(CHUNQIU_FILE)
        return

    print(f"✓ 找到：《春秋》原始 JSON")

    # ========================================================
    # 2. 读取 normalized_corpus.json
    # ========================================================

    print("\n【2】读取 normalized_corpus.json")

    try:
        with open(
            NORMALIZED_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            normalized_data = json.load(f)

        print(
            f"✓ 读取成功：{len(normalized_data)} 条"
        )

    except Exception as e:

        print("✗ 读取失败：", e)
        return

    # ========================================================
    # 3. 找出 normalized 中异常的 13 条
    # ========================================================

    print("\n【3】寻找《春秋》异常记录")

    missing_chinese = []
    missing_french = []

    for index, record in enumerate(normalized_data):

        if record.get("book") != "春秋":
            continue

        chinese_empty = is_empty(
            record.get("chinese")
        )

        french_empty = is_empty(
            record.get("french")
        )

        if chinese_empty:
            missing_chinese.append(
                (index, record)
            )

        if french_empty:
            missing_french.append(
                (index, record)
            )

    print(
        f"中文为空：《春秋》{len(missing_chinese)} 条"
    )

    print(
        f"法文为空：《春秋》{len(missing_french)} 条"
    )

    # ========================================================
    # 4. 显示异常记录 ID
    # ========================================================

    print("\n【4】异常记录 ID")

    print("\n中文为空：")

    for index, record in missing_chinese:

        print(
            f"  索引 {index} | "
            f"ID {record.get('id')} | "
            f"章节 {record.get('chapter')}"
        )

    print("\n法文为空：")

    for index, record in missing_french:

        print(
            f"  索引 {index} | "
            f"ID {record.get('id')} | "
            f"章节 {record.get('chapter')}"
        )

    # ========================================================
    # 5. 读取《春秋》原始 JSON
    # ========================================================

    print("\n【5】读取《春秋》原始 JSON")

    try:

        with open(
            CHUNQIU_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            chunqiu_data = json.load(f)

        print(
            f"✓ 原始数据读取成功："
            f"{len(chunqiu_data)} 条"
        )

    except Exception as e:

        print("✗ 《春秋》JSON 读取失败：", e)
        return

    # ========================================================
    # 6. 建立 ID 索引
    # ========================================================

    print("\n【6】建立《春秋》原始数据 ID 索引")

    chunqiu_by_id = {}

    duplicate_ids = []

    for record in chunqiu_data:

        record_id = record.get("id")

        if record_id in chunqiu_by_id:

            duplicate_ids.append(record_id)

        else:

            chunqiu_by_id[record_id] = record

    print(
        f"原始数据 ID 数量：{len(chunqiu_by_id)}"
    )

    if duplicate_ids:

        print(
            f"⚠ 原始数据存在重复 ID："
            f"{len(duplicate_ids)} 个"
        )

        print(
            "重复 ID：",
            duplicate_ids[:20]
        )

    else:

        print("✓ 原始数据 ID 全部唯一")

    # ========================================================
    # 7. 检查 12 条中文为空的数据
    # ========================================================

    print("\n【7】检查 12 条中文为空的数据")

    found_missing_chinese = 0
    chinese_source_problem = 0

    for index, normalized_record in missing_chinese:

        record_id = normalized_record.get("id", "")

        # 从 chunqiu_0562 提取数字 562
        if str(record_id).startswith("chunqiu_"):

            try:
                original_id = int(
                    str(record_id).split("_")[1]
                )
            except Exception:
                original_id = None

        else:

            original_id = None

        print("\n")
        print("=" * 70)
        print(
            f"异常记录：{record_id}"
        )

        print(
            f"normalized_corpus.json 原始索引：{index}"
        )

        # ----------------------------------------------------
        # 找原始数据
        # ----------------------------------------------------

        original_record = None

        if original_id is not None:

            original_record = chunqiu_by_id.get(
                original_id
            )

        if original_record is None:

            print(
                "✗ 在《春秋》原始 JSON 中没有找到对应 ID"
            )

            continue

        found_missing_chinese += 1

        print(
            f"✓ 找到原始 ID：{original_id}"
        )

        print_record(
            "【normalized_corpus.json】",
            normalized_record
        )

        print_record(
            "【chunqiu_corpus.json 原始数据】",
            original_record
        )

        # ----------------------------------------------------
        # 比较关键字段
        # ----------------------------------------------------

        print("\n【字段对比】")

        fields = [
            "book",
            "juan",
            "duke_cn",
            "year_cn",
            "year_bc",
            "chinese",
            "french"
        ]

        for field in fields:

            normalized_value = normalized_record.get(
                field,
                ""
            )

            original_value = original_record.get(
                field,
                ""
            )

            if normalized_value == original_value:

                print(
                    f"  ✓ {field}：一致"
                )

            else:

                print(
                    f"  ⚠ {field}：存在差异"
                )

                print(
                    "      normalized：",
                    repr(normalized_value)
                )

                print(
                    "      original：",
                    repr(original_value)
                )

        # ----------------------------------------------------
        # 判断源数据是否也为空
        # ----------------------------------------------------

        original_chinese = original_record.get(
            "chinese",
            ""
        )

        if is_empty(original_chinese):

            print(
                "\n>>> 判断："
                "《春秋》原始 JSON 中中文本身就是空的。"
            )

            print(
                ">>> 这不是 normalize_corpus.py 丢失的数据。"
            )

        else:

            print(
                "\n>>> ⚠ 判断："
                "原始 JSON 有中文，但 normalized 中为空！"
            )

            print(
                ">>> 这说明 normalize_corpus.py "
                "可能存在字段读取或转换问题。"
            )

            chinese_source_problem += 1

    # ========================================================
    # 8. 检查 1 条法文为空的数据
    # ========================================================

    print("\n【8】检查 1 条法文为空的数据")

    found_missing_french = 0
    french_source_problem = 0

    for index, normalized_record in missing_french:

        record_id = normalized_record.get("id", "")

        if str(record_id).startswith("chunqiu_"):

            try:

                original_id = int(
                    str(record_id).split("_")[1]
                )

            except Exception:

                original_id = None

        else:

            original_id = None

        print("\n")
        print("=" * 70)

        print(
            f"异常记录：{record_id}"
        )

        print(
            f"normalized_corpus.json 原始索引：{index}"
        )

        original_record = None

        if original_id is not None:

            original_record = chunqiu_by_id.get(
                original_id
            )

        if original_record is None:

            print(
                "✗ 在《春秋》原始 JSON 中没有找到对应 ID"
            )

            continue

        found_missing_french += 1

        print(
            f"✓ 找到原始 ID：{original_id}"
        )

        print_record(
            "【normalized_corpus.json】",
            normalized_record
        )

        print_record(
            "【chunqiu_corpus.json 原始数据】",
            original_record
        )

        print("\n【字段对比】")

        fields = [
            "book",
            "juan",
            "duke_cn",
            "year_cn",
            "year_bc",
            "chinese",
            "french"
        ]

        for field in fields:

            normalized_value = normalized_record.get(
                field,
                ""
            )

            original_value = original_record.get(
                field,
                ""
            )

            if normalized_value == original_value:

                print(
                    f"  ✓ {field}：一致"
                )

            else:

                print(
                    f"  ⚠ {field}：存在差异"
                )

                print(
                    "      normalized：",
                    repr(normalized_value)
                )

                print(
                    "      original：",
                    repr(original_value)
                )

        original_french = original_record.get(
            "french",
            ""
        )

        if is_empty(original_french):

            print(
                "\n>>> 判断："
                "《春秋》原始 JSON 中法文本身就是空的。"
            )

            print(
                ">>> 这不是 normalize_corpus.py 丢失的数据。"
            )

        else:

            print(
                "\n>>> ⚠ 判断："
                "原始 JSON 有法文，但 normalized 中为空！"
            )

            print(
                ">>> 这说明 normalize_corpus.py "
                "可能存在字段读取或转换问题。"
            )

            french_source_problem += 1

    # ========================================================
    # 9. 检查 ID 映射是否完整
    # ========================================================

    print("\n【9】检查 ID 映射")

    all_missing_records = (
        missing_chinese +
        missing_french
    )

    # 去重
    checked_ids = set()

    not_found_ids = []

    for index, record in all_missing_records:

        record_id = record.get("id", "")

        if record_id in checked_ids:
            continue

        checked_ids.add(record_id)

        if str(record_id).startswith("chunqiu_"):

            try:

                original_id = int(
                    str(record_id).split("_")[1]
                )

            except Exception:

                original_id = None

            if original_id not in chunqiu_by_id:

                not_found_ids.append(
                    (record_id, original_id)
                )

    print(
        f"需要检查的异常记录："
        f"{len(checked_ids)} 条"
    )

    print(
        f"成功找到原始记录："
        f"{len(checked_ids) - len(not_found_ids)} 条"
    )

    print(
        f"找不到原始记录："
        f"{len(not_found_ids)} 条"
    )

    if not_found_ids:

        print("\n找不到的 ID：")

        for record_id, original_id in not_found_ids:

            print(
                f"  {record_id} "
                f"(原始 ID={original_id})"
            )

    # ========================================================
    # 10. 最终判断
    # ========================================================

    print("\n")
    print("=" * 70)
    print("最终判断")
    print("=" * 70)

    print(
        f"中文为空记录：{len(missing_chinese)} 条"
    )

    print(
        f"法文为空记录：{len(missing_french)} 条"
    )

    print(
        f"中文源数据异常：{chinese_source_problem} 条"
    )

    print(
        f"法文源数据异常：{french_source_problem} 条"
    )

    print(
        f"无法找到原始记录：{len(not_found_ids)} 条"
    )

    print()

    if (
        chinese_source_problem == 0
        and french_source_problem == 0
        and len(not_found_ids) == 0
    ):

        print(
            "✓ 检查结果："
            "这 13 条缺失数据均可在源数据中确认。"
        )

        print()
        print(
            "✓ normalized_corpus.json "
            "没有因为标准化过程而丢失这 13 条内容。"
        )

        print()
        print(
            "下一步应该决定："
        )

        print(
            "1. 是否保留这些原始缺失记录；"
        )

        print(
            "2. 是否从其他可靠版本补齐；"
        )

        print(
            "3. 是否在 RAG 检索时排除中文或法文为空的记录。"
        )

    else:

        print(
            "⚠ 检查发现标准化过程中可能存在数据问题。"
        )

        print(
            "暂时不要重新生成最终数据库，"
            "先根据上面的字段差异继续处理。"
        )

    print("\n" + "=" * 70)
    print("检查完成")
    print("=" * 70)


if __name__ == "__main__":
    main()