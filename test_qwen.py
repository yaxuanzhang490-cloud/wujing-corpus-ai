import os
from dashscope import Generation


def main():

    print("=" * 60)
    print("通义千问 API 测试")
    print("=" * 60)

    # 从 Windows 环境变量读取 API Key
    api_key = os.getenv("DASHSCOPE_API_KEY")

    if not api_key:
        print("❌ 没有找到 DASHSCOPE_API_KEY")
        print("请检查 API Key 是否已经配置到环境变量。")
        return

    print("✓ API Key 已读取")
    print("正在请求通义千问……")
    print()

    messages = [
        {
            "role": "system",
            "content": "你是一个帮助用户学习中国古代典籍的助手。"
        },
        {
            "role": "user",
            "content": "请简单介绍一下《易经》。"
        }
    ]

    try:

        response = Generation.call(
            api_key=api_key,
            model="qwen-plus",
            messages=messages,
            result_format="message"
        )

        if response.status_code == 200:

            answer = response.output.choices[0].message.content

            print("✓ 通义千问调用成功！")
            print()
            print("AI 回答：")
            print("-" * 60)
            print(answer)
            print("-" * 60)

        else:

            print("❌ API 调用失败")
            print(f"HTTP 状态码：{response.status_code}")
            print(f"错误代码：{response.code}")
            print(f"错误信息：{response.message}")

    except Exception as e:

        print("❌ 程序运行出现异常")
        print()
        print(e)


if __name__ == "__main__":
    main()