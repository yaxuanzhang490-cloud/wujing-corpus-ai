import pandas as pd
from pathlib import Path

# ============================================================
# 《易经》古籍语料库结构完整性检查
# ============================================================

print("=" * 60)
print("开始进行《易经》语料库结构完整性检查")
print("=" * 60)

# Excel 文件路径
excel_path = Path(__file__).parent.parent / "data" / "易经_结构化工作版.xlsx"

print(f"\n正在读取：{excel_path}")

if not excel_path.exists():
    print("✗ Excel 文件不存在！")
    print(f"请检查路径：{excel_path}")
    exit()

df = pd.read_excel(
    excel_path,
    sheet_name="structured_corpus"
)

print(f"✓ 成功读取，共 {len(df)} 条数据")


# ============================================================
# 1. 数据类型分布
# ============================================================

print("\n" + "=" * 60)
print("【1. 数据类型分布】")
print("=" * 60)

print(df["type"].value_counts().to_string())


# ============================================================
# 2. 检查卦号
# ============================================================

print("\n" + "=" * 60)
print("【2. 卦号完整性检查】")
print("=" * 60)

hexagram_numbers = sorted(df["hexagram_no"].dropna().unique())

print(f"卦号数量：{len(hexagram_numbers)}")

if hexagram_numbers == list(range(1, 65)):
    print("✓ 1–64 卦完整")
else:
    print("⚠ 卦号存在异常：")
    print(hexagram_numbers)


# ============================================================
# 3. 检查每一卦的基本结构
# ============================================================

print("\n" + "=" * 60)
print("【3. 每卦结构检查】")
print("=" * 60)

structure_errors = []

for hex_no in range(1, 65):

    group = df[df["hexagram_no"] == hex_no]

    hex_name = group["hexagram"].iloc[0] if len(group) > 0 else "未知"

    # 普通爻辞
    yao_count = len(group[group["type"] == "爻辞"])

    # 卦辞
    guaci_count = len(group[group["type"] == "卦辞"])

    # 特殊爻辞
    special_count = len(group[group["type"] == "特殊爻辞"])

    # 普通爻辞必须正好 6 条
    if yao_count != 6:
        structure_errors.append(
            f"第 {hex_no} 卦「{hex_name}」：普通爻辞 {yao_count} 条，应为 6 条"
        )

    # 一般卦辞为 1 条
    # 第 41 卦「损」的卦辞拆成 2 行，是允许的
    if hex_no == 41:
        if guaci_count != 2:
            structure_errors.append(
                f"第 41 卦「损」：卦辞 {guaci_count} 条，应为 2 条"
            )
    else:
        if guaci_count != 1:
            structure_errors.append(
                f"第 {hex_no} 卦「{hex_name}」：卦辞 {guaci_count} 条，应为 1 条"
            )

    # 只有乾、坤允许特殊爻辞
    if hex_no in [1, 2]:
        if special_count != 1:
            structure_errors.append(
                f"第 {hex_no} 卦「{hex_name}」：特殊爻辞 {special_count} 条，应为 1 条"
            )
    else:
        if special_count != 0:
            structure_errors.append(
                f"第 {hex_no} 卦「{hex_name}」：存在异常特殊爻辞 {special_count} 条"
            )


if len(structure_errors) == 0:
    print("✓ 64 卦结构全部正常")
else:
    print("⚠ 发现结构问题：")
    for error in structure_errors:
        print("  - " + error)


# ============================================================
# 4. 检查卦辞
# ============================================================

print("\n" + "=" * 60)
print("【4. 卦辞完整性检查】")
print("=" * 60)

guaci_counts = df.groupby(
    ["hexagram_no", "hexagram"]
)["type"].apply(
    lambda x: (x == "卦辞").sum()
)

print("各卦卦辞数量：")
print(guaci_counts.to_string())

print("\n特殊情况：")

special_guaci = guaci_counts[guaci_counts != 1]

if len(special_guaci) == 0:
    print("✓ 每卦均有 1 条卦辞")
else:
    for index, count in special_guaci.items():
        hex_no, hex_name = index

        if hex_no == 41 and count == 2:
            print("✓ 第 41 卦「损」卦辞拆分为 2 条，属于正常情况")
        else:
            print(f"⚠ 第 {hex_no} 卦「{hex_name}」卦辞数量异常：{count}")


# ============================================================
# 5. 检查普通爻辞
# ============================================================

print("\n" + "=" * 60)
print("【5. 普通爻辞数量检查】")
print("=" * 60)

yao_counts = df[df["type"] == "爻辞"].groupby(
    ["hexagram_no", "hexagram"]
).size()

print("各卦普通爻辞数量分布：")
print(yao_counts.value_counts().sort_index().to_string())

if all(yao_counts == 6):
    print("✓ 所有 64 卦均有 6 条普通爻辞")
else:
    print("⚠ 存在普通爻辞数量异常的卦")


# ============================================================
# 6. 检查特殊爻辞
# ============================================================

print("\n" + "=" * 60)
print("【6. 特殊爻辞检查】")
print("=" * 60)

special = df[df["type"] == "特殊爻辞"]

if len(special) == 2:
    print("✓ 共发现 2 条特殊爻辞")
    print(special[
        ["id", "hexagram_no", "hexagram", "position", "chinese"]
    ].to_string(index=False))
else:
    print(f"⚠ 特殊爻辞数量为 {len(special)} 条")


# ============================================================
# 7. position 字段检查
# ============================================================

print("\n" + "=" * 60)
print("【7. position 字段检查】")
print("=" * 60)

print(df["position"].fillna("(空)").value_counts().to_string())

print("\n✓ position 字段检查完成")


# ============================================================
# 8. 中文原文重复检查
# ============================================================

print("\n" + "=" * 60)
print("【8. 中文原文重复检查】")
print("=" * 60)

duplicate_chinese = df[
    df["chinese"].duplicated(keep=False)
]

if len(duplicate_chinese) == 0:
    print("✓ 没有重复中文原文")
else:
    print(f"⚠ 发现 {len(duplicate_chinese)} 条重复中文原文")
    print(
        duplicate_chinese[
            ["id", "hexagram_no", "hexagram", "chinese"]
        ].to_string(index=False)
    )


# ============================================================
# 9. ID 检查
# ============================================================

print("\n" + "=" * 60)
print("【9. ID 检查】")
print("=" * 60)

if df["id"].is_unique:
    print("✓ ID 全部唯一")
else:
    print("⚠ 存在重复 ID")


# ============================================================
# 10. 最终总结
# ============================================================

print("\n" + "=" * 60)
print("结构检查完成")
print("=" * 60)

print(f"""
总数据量：{len(df)}
卦数：{df["hexagram"].nunique()}
卦辞行数：{len(df[df["type"] == "卦辞"])}
普通爻辞行数：{len(df[df["type"] == "爻辞"])}
特殊爻辞行数：{len(df[df["type"] == "特殊爻辞"])}
""")

print("=" * 60)

if len(structure_errors) == 0:
    print("✓ 《易经》语料库结构检查通过！")
    print("✓ 可以进入 SQLite 数据库构建阶段。")
else:
    print("⚠ 结构检查发现问题，请进一步检查。")

print("=" * 60)