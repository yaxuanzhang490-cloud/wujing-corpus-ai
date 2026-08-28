# ============================================================
# 五经古典语料库
# RAG 服务层
#
# 作用：
# 1. 调用 rag_retriever.py
# 2. 对外提供统一的 RAG 检索接口
# 3. 不再自己实现检索算法
#
# 真正的检索逻辑由：
#     rag_retriever.py
# 负责
# ============================================================


from rag_retriever import retrieve


# ============================================================
# RAG 检索接口
# ============================================================

def search(
    query: str,
    top_k: int = 8
):
    """
    对外提供统一的 RAG 检索接口。

    参数：
        query  : 用户的问题
        top_k  : 返回最多多少条语料

    返回：
        rag_retriever.retrieve() 返回的完整结果
    """

    return retrieve(
        query=query,
        top_k=top_k
    )


# ============================================================
# 为旧代码保留一个兼容接口
# ============================================================

def search_corpus(
    query: str,
    top_k: int = 8
):
    """
    兼容旧版本代码。

    如果其他程序之前调用：

        search_corpus(query)

    现在仍然可以正常工作。

    实际检索仍然交给 rag_retriever.py。
    """

    return retrieve(
        query=query,
        top_k=top_k
    )


# ============================================================
# 简单测试
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("五经古典语料库 - RAG 服务层测试")
    print("=" * 60)

    print()
    print("当前检索核心：rag_retriever.py")
    print()

    while True:

        query = input(
            "请输入检索问题（输入 q 退出）："
        ).strip()

        if query.lower() == "q":
            print("退出测试。")
            break

        if not query:
            continue

        try:

            result = search(
                query=query,
                top_k=8
            )

            print()
            print("=" * 60)
            print("RAG 检索结果")
            print("=" * 60)

            print(
                f"问题：{result.get('query', query)}"
            )

            analysis = result.get(
                "analysis",
                {}
            )

            print(
                f"典籍：{analysis.get('books', [])}"
            )

            print(
                f"卦名：{analysis.get('hexagrams', [])}"
            )

            print(
                f"爻位：{analysis.get('positions', [])}"
            )

            print(
                f"关键词：{analysis.get('keywords', [])}"
            )

            results = result.get(
                "results",
                []
            )

            print()
            print(
                f"检索结果：{len(results)} 条"
            )

            for i, item in enumerate(
                results,
                start=1
            ):

                record = item.get(
                    "record",
                    {}
                )

                print()
                print(
                    f"【结果 {i}】"
                )

                print(
                    f"相关度：{item.get('score', 0)}"
                )

                print(
                    f"典籍："
                    f"{record.get('book', '')}"
                )

                print(
                    f"章节："
                    f"{record.get('chapter', '')}"
                )

                if record.get("position"):

                    print(
                        f"位置："
                        f"{record.get('position')}"
                    )

                print(
                    f"类型："
                    f"{record.get('type', '')}"
                )

                print(
                    f"中文："
                    f"{record.get('chinese', '')}"
                )

                print(
                    f"法文："
                    f"{record.get('french', '')}"
                )

                print(
                    f"来源："
                    f"{record.get('source', '')}"
                )

                print(
                    "-" * 60
                )

        except Exception as e:

            print()
            print(
                "✗ RAG 检索失败："
            )

            print(e)