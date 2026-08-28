import pandas as pd

# Excel 文件的位置
excel_path = r"C:\Users\ASUS\Desktop\古籍语料库\data\易经_结构化工作版.xlsx"

print("=" * 60)
print("开始检查《易经》Excel")
print("=" * 60)

# 读取 Excel
excel_file = pd.ExcelFile(excel_path)

# 查看所有工作表
print("\n【1. 工作表】")
print(excel_file.sheet_names)

# 逐个检查工作表
for sheet_name in excel_file.sheet_names:

    print("\n" + "=" * 60)
    print(f"【2. 工作表：{sheet_name}】")
    print("=" * 60)

    df = pd.read_excel(
        excel_path,
        sheet_name=sheet_name
    )

    print(f"\n行数：{len(df)}")
    print(f"列数：{len(df.columns)}")

    print("\n列名：")
    for i, column in enumerate(df.columns):
        print(f"  {i + 1}. {column}")

    print("\n前 5 条数据：")
    print(df.head().to_string())

print("\n" + "=" * 60)
print("检查完成！")
print("=" * 60)