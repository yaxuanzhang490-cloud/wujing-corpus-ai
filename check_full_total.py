import json
from collections import Counter


# ============================================================
# full_total.json 数据完整性检查工具
# ============================================================

FILE_PATH = "full_total.json"


def main():

    print("=" * 70)
    print("五经古典语料库 - full_total.json 数据检查")
    print("=" * 70)

    # ========================================================
    # 1. 读取 JSON
    # ========================================================

    print()
    print("【1】检查 JSON 文件")

    try:

        with open(
            FILE_PATH,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        print("✓ JSON 文件读取成功")

    except Exception as e:

        print("❌ JSON 文件读取失败")
        print("错误：", e)
        return

    # ========================================================
    # 2. 基本信息
    # ========================================================

    print()
    print("【2】基本信息")

    print("总记录数：", len(data))

    if not isinstance(data, list):

        print("❌ JSON 顶层结构不是 list")
        return

    print("顶层结构：list ✓")

    # ========================================================
    # 3. 字段统计
    # ========================================================

    print()
    print("【3】book 字段统计")

    book_counter = Counter(
        str(item.get("book", "")).strip()
        for item in data
        if isinstance(item, dict)
    )

    for book, count in book_counter.most_common():

        if book:

            print(
                f"  {book}: {count} 条"
            )

        else:

            print(
                f"  【空 book】: {count} 条"
            )

    # ========================================================
    # 4. 中文 / 法文完整性
    # ========================================================

    print()
    print("【4】中文与法文完整性")

    empty_chinese = []
    empty_french = []

    for index, item in enumerate(data):

        chinese = str(
            item.get("chinese", "")
        ).strip()

        french = str(
            item.get("french", "")
        ).strip()

        if not chinese:

            empty_chinese.append(index)

        if not french:

            empty_french.append(index)

    print(
        f"中文为空：{len(empty_chinese)} 条"
    )

    print(
        f"法文为空：{len(empty_french)} 条"
    )

    # ========================================================
    # 5. 找出空数据的具体结构
    # ========================================================

    print()
    print("【5】检查空中文 + 空法文记录")

    empty_records = []

    for index, item in enumerate(data):

        chinese = str(
            item.get("chinese", "")
        ).strip()

        french = str(
            item.get("french", "")
        ).strip()

        if not chinese and not french:

            empty_records.append(
                (index, item)
            )

    print(
        f"同时缺少中文和法文：{len(empty_records)} 条"
    )

    # 只展示前 20 条
    show_count = min(
        20,
        len(empty_records)
    )

    print()
    print(
        f"下面显示前 {show_count} 条异常记录："
    )

    for index, item in empty_records[:show_count]:

        print()
        print(
            f"--- 原始索引 {index} ---"
        )

        print(item)

    # ========================================================
    # 6. 检查易经混入情况
    # ========================================================

    print()
    print("【6】检查《易经》混入情况")

    yijing_records = []

    for index, item in enumerate(data):

        book = str(
            item.get("book", "")
        ).strip()

        if book == "易经":

            yijing_records.append(
                (index, item)
            )

    print(
        f"发现《易经》记录：{len(yijing_records)} 条"
    )

    for index, item in yijing_records[:10]:

        print()
        print(
            f"--- 原始索引 {index} ---"
        )

        print(item)

    # ========================================================
    # 7. 检查字段结构
    # ========================================================

    print()
    print("【7】字段结构检查")

    all_keys = Counter()

    for item in data:

        if isinstance(item, dict):

            key_signature = tuple(
                sorted(item.keys())
            )

            all_keys[key_signature] += 1

    print(
        f"发现 {len(all_keys)} 种不同字段结构"
    )

    for i, (keys, count) in enumerate(
        all_keys.most_common(),
        start=1
    ):

        print()
        print(
            f"结构 {i}：{count} 条"
        )

        print(
            "字段：",
            list(keys)
        )

        if i >= 10:
            break

    # ========================================================
    # 8. 检查重复记录
    # ========================================================

    print()
    print("【8】重复记录检查")

    seen = {}
    duplicates = []

    for index, item in enumerate(data):

        try:

            key = json.dumps(
                item,
                ensure_ascii=False,
                sort_keys=True
            )

        except Exception:

            continue

        if key in seen:

            duplicates.append(
                (index, seen[key])
            )

        else:

            seen[key] = index

    print(
        f"发现完全重复记录：{len(duplicates)} 条"
    )

    if duplicates:

        print()
        print("前 10 组重复记录：")

        for current, original in duplicates[:10]:

            print(
                f"  原始索引 {original} "
                f"<-> 重复索引 {current}"
            )

    # ========================================================
    # 9. 检查 ID
    # ========================================================

    print()
    print("【9】ID 字段检查")

    ids = []
    empty_ids = []

    for index, item in enumerate(data):

        item_id = item.get("id")

        if item_id is None:

            empty_ids.append(index)

        else:

            ids.append(str(item_id))

    print(
        f"存在 id 的记录：{len(ids)} 条"
    )

    print(
        f"缺少 id 的记录：{len(empty_ids)} 条"
    )

    id_counter = Counter(ids)

    duplicate_ids = [
        (item_id, count)
        for item_id, count
        in id_counter.items()
        if count > 1
    ]

    print(
        f"重复 id：{len(duplicate_ids)} 个"
    )

    if duplicate_ids:

        print()
        print("前 20 个重复 ID：")

        for item_id, count in duplicate_ids[:20]:

            print(
                f"  id={item_id} → {count} 次"
            )

    # ========================================================
    # 10. 检查关键字段
    # ========================================================

    print()
    print("【10】关键字段检查")

    fields = [
        "id",
        "id_sub",
        "book",
        "chapter",
        "chinese",
        "french"
    ]

    for field in fields:

        count = sum(
            1
            for item in data
            if field in item
        )

        print(
            f"  {field}: {count}/{len(data)} 条存在"
        )

    # ========================================================
    # 结束
    # ========================================================

    print()
    print("=" * 70)
    print("检查完成")
    print("=" * 70)


if __name__ == "__main__":

    main()