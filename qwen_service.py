import os
from dashscope import Generation


# ============================================================
# 通义千问服务
# ============================================================

def ask_qwen(question):

    api_key = os.getenv("DASHSCOPE_API_KEY")

    if not api_key:
        raise RuntimeError(
            "没有找到 DASHSCOPE_API_KEY，请检查环境变量是否配置正确。"
        )

    messages = [
        {
            "role": "system",
            "content": (
                "你是一个帮助用户学习中国古代典籍的助手。"
                "你需要准确、清晰地回答用户关于中国古代典籍的问题。"
            )
        },
        {
            "role": "user",
            "content": question
        }
    ]

    response = Generation.call(
        api_key=api_key,
        model="qwen-plus",
        messages=messages,
        result_format="message"
    )

    if response.status_code == 200:

        return response.output.choices[0].message.content

    else:

        raise RuntimeError(
            f"通义千问 API 调用失败："
            f"{response.status_code} "
            f"{response.code} "
            f"{response.message}"
        )


# ============================================================
# 本地测试
# ============================================================

if __name__ == "__main__":

    question = "请简单介绍一下《易经》。"

    answer = ask_qwen(question)

    print("=" * 60)
    print("通义千问测试")
    print("=" * 60)

    print("问题：")
    print(question)

    print("\nAI回答：")
    print(answer)

    print("=" * 60)