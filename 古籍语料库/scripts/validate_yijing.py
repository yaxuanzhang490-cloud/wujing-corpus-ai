import pandas as pd
from pathlib import Path

# ============================================================
# 《易经》古籍语料库数据质量检查
# ============================================================

print("=" * 60)
print("开始进行《易经》数据质量检查")
print("=" * 60)

# Excel 文件路径
excel_path = Path(
    r"C:\Users\ASUS\Desktop\古籍语料库\data\易经_结构化工作版.xlsx"
)

print(f"\n正在读取：{excel_path}")

# 检查文件是否真的存在
if not excel_path.exists():
    print("\n❌ 错误：找不到 Excel 文件！")
    print(f"实际检查的路径：{excel_path}")
    print("\n请检查这个文件是否存在：")
    print(r"C:\Users\ASUS\Desktop\古籍语料库\data\易经_结构化工作版.xlsx")
    exit()

print("✓ Excel 文件存在")

# 读取 Excel
df = pd.read_excel(
    excel_path,
    sheet_name="structured_corpus"
)

print(f"✓ 成功读取，共 {len(df)} 条数据。")


# ============================================================
# 1. 检查 ID
# ============================================================

print("\n" + "=" * 60)
print("【1. ID 检查】")
print("=" * 60)

print(f"ID 数量：{df['id'].nunique()}")
print(f"数据行数：{len(df)}")

duplicate_ids = df[df["id"].duplicated(keep=False)]

if len(duplicate_ids) == 0:
    print("✓ 没有重复 ID")
else:
    print("⚠ 发现重复 ID：")
    print(
        duplicate_ids[
            ["id", "chinese"]
        ].to_string(index=False)
    )


# ============================================================
# 2. 检查中文原文
# ============================================================

print("\n" + "=" * 60)
print("【2. 中文原文检查】")
print("=" * 60)

missing_chinese = df[
    df["chinese"].isna()
    | (df["chinese"].astype(str).str.strip() == "")
]

print(f"中文原文缺失：{len(missing_chinese)} 条")

if len(missing_chinese) > 0:
    print("\n缺失中文原文的数据：")
    print(
        missing_chinese[
            [
                "id",
                "hexagram_no",
                "hexagram",
                "type",
                "position",
                "chinese"
            ]
        ].to_string(index=False)
    )
else:
    print("✓ 中文原文没有明显缺失")


# ============================================================
# 3. 检查法文翻译
# ============================================================

print("\n" + "=" * 60)
print("【3. 法文翻译检查】")
print("=" * 60)

missing_french = df[
    df["french"].isna()
    | (df["french"].astype(str).str.strip() == "")
]

print(f"法文翻译缺失：{len(missing_french)} 条")

if len(missing_french) > 0:
    print("\n缺失法文的数据：")
    print(
        missing_french[
            [
                "id",
                "hexagram_no",
                "hexagram",
                "type",
                "position",
                "chinese"
            ]
        ].to_string(index=False)
    )
else:
    print("✓ 法文翻译没有明显缺失")


# ============================================================
# 4. 检查卦号范围
# ============================================================

print("\n" + "=" * 60)
print("【4. 卦号检查】")
print("=" * 60)

invalid_hexagrams = df[
    ~df["hexagram_no"].between(1, 64)
]

if len(invalid_hexagrams) == 0:
    print("✓ 所有卦号均在 1–64 范围内")
else:
    print("⚠ 发现异常卦号：")
    print(
        invalid_hexagrams[
            ["id", "hexagram_no", "hexagram", "position"]
        ].to_string(index=False)
    )


# ============================================================
# 5. 检查卦名
# ============================================================

print("\n" + "=" * 60)
print("【5. 卦名检查】")
print("=" * 60)

hexagram_count = df["hexagram"].nunique()

print(f"不同卦名数量：{hexagram_count}")

if hexagram_count == 64:
    print("✓ 正好包含 64 个卦")
else:
    print("⚠ 卦名数量不是 64，请进一步检查")


# ============================================================
# 6. 检查每一卦的数据量
# ============================================================

print("\n" + "=" * 60)
print("【6. 每卦数据量检查】")
print("=" * 60)

counts = df.groupby(
    ["hexagram_no", "hexagram"]
).size()

print("每卦数据量统计：")
print(counts.to_string())

print("\n数据量分布：")
print(counts.value_counts().sort_index().to_string())


# ============================================================
# 7. 检查特殊字符 / 缺失标记
# ============================================================

print("\n" + "=" * 60)
print("【7. 可疑缺失字符检查】")
print("=" * 60)

patterns = [
    "□",
    "???",
    "？？？",
    "缺失",
    "待补",
    "未译",
    "N/A"
]

for pattern in patterns:

    result = df[
        df["chinese"].astype(str).str.contains(
            pattern,
            regex=False,
            na=False
        )
    ]

    if len(result) > 0:
        print(f"\n⚠ 发现 {pattern}：{len(result)} 条")

        print(
            result[
                [
                    "id",
                    "hexagram_no",
                    "hexagram",
                    "position",
                    "chinese",
                    "french"
                ]
            ].to_string(index=False)
        )


# ============================================================
# 8. 最终总结
# ============================================================

print("\n" + "=" * 60)
print("检查完成")
print("=" * 60)

print(f"""
总数据量：{len(df)}
不同卦数：{df['hexagram'].nunique()}
中文缺失：{len(missing_chinese)}
法文缺失：{len(missing_french)}
重复 ID：{len(duplicate_ids)}
""")

print("=" * 60)
print("请把上面的完整输出发给我。")
print("我们根据检查结果决定是否进入 SQLite 数据库构建。")
print("=" * 60)