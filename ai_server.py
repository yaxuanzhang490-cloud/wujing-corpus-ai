import os
import json
import csv
import io
import openpyxl

from dotenv import load_dotenv

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from qwen_service import ask_qwen
from rag_service import search_corpus

# 加载项目根目录下的 .env
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


# ============================================================
# 五经古典语料库 AI 服务
#
# 功能：
# 1. 调用五经语料库进行检索
# 2. 将检索结果提供给通义千问
# 3. 通义千问可以结合自身知识进行回答
# 4. 语料库只是 AI 的参考资料之一，而不是唯一知识来源
# ============================================================


app = Flask(__name__)

# 允许前端网页访问 AI 服务
CORS(app)


# ============================================================
# 首页
# ============================================================

@app.route("/")
def index():

    return send_from_directory(
        os.path.dirname(os.path.abspath(__file__)),
        "index.html"
    )


# ============================================================
# AI 问答接口
# ============================================================

@app.route("/api/ask", methods=["POST"])
def api_ask():

    try:

        # ====================================================
        # 第一步：获取用户问题
        # ====================================================

        data = request.get_json()

        if not data:

            return jsonify({
                "success": False,
                "error": "没有收到请求数据"
            }), 400


        question = data.get("question", "").strip()


        if not question:

            return jsonify({
                "success": False,
                "error": "问题不能为空"
            }), 400


        print()
        print("=" * 70)
        print("收到用户问题：")
        print(question)
        print("=" * 70)


                # ====================================================
        # 第二步：检索五经语料库
        # ====================================================

        print("正在检索五经语料库……")


        try:

            rag_result = search_corpus(
                question,
                top_k=5
            )

            # ------------------------------------------------
            # rag_service.py 返回的是完整的 RAG 结果对象
            #
            # 真正的检索结果位于：
            #
            # rag_result["results"]
            # ------------------------------------------------

            results = rag_result.get(
                "results",
                []
            )

            analysis = rag_result.get(
                "analysis",
                {}
            )


        except Exception as e:

            print("⚠️ 语料库检索出现异常：")
            print(e)

            results = []

            analysis = {}


        print(
            f"✓ 五经语料库检索到 {len(results)} 条相关资料"
        )


        if analysis:

            print(
                f"  典籍：{analysis.get('books', [])}"
            )

            print(
                f"  卦名：{analysis.get('hexagrams', [])}"
            )

            print(
                f"  爻位：{analysis.get('positions', [])}"
            )

            print(
                f"  公：{analysis.get('dukes', [])}"
            )

            print(
                f"  卷：{analysis.get('juans', [])}"
            )

            print(
                f"  年份：{analysis.get('years', [])}"
            )

            print(
                f"  关键词：{analysis.get('keywords', [])}"
            )

                # ====================================================
        # 第三步：整理语料库资料
        # ====================================================

        context_parts = []


        for i, item in enumerate(
            results,
            start=1
        ):

            record = item.get(
                "record",
                {}
            )

            score = item.get(
                "score",
                0
            )


            book = (
                record.get("book")
                or ""
            )

            chapter = (
                record.get("chapter")
                or ""
            )

            position = (
                record.get("position")
                or ""
            )

            item_type = (
                record.get("type")
                or ""
            )

            chinese = (
                record.get("chinese")
                or ""
            )

            french = (
                record.get("french")
                or ""
            )

            source = (
                record.get("source")
                or ""
            )


            text = f"""
【语料 {i}】
相关度：{score}
来源：{source}
典籍：{book}
章节：{chapter}
类型：{item_type}
位置：{position}
中文原文：{chinese}
法文翻译：{french}
"""


            context_parts.append(
                text
            )


        context = "\n".join(
            context_parts
        )

        # ====================================================
        # 第四步：构造 AI 提示词
        #
        # 这里是这次修改最重要的地方。
        #
        # 不再要求：
        #
        #     “只能根据语料库回答”
        #
        # 而是要求：
        #
        #     “语料库 + AI 自身知识综合回答”
        #
        # 这样千问就不会因为 RAG 没搜到资料，
        # 就拒绝回答。
        # ====================================================


        if context:

            prompt = f"""
你是“五经古典语料库”的智能 AI 学习助手。

你拥有两类信息来源：

第一类：你自身已经具备的通用知识、语言理解能力、推理能力和分析能力。

第二类：下面提供的“五经古典语料库”检索结果。

你的任务不是机械地复述语料库，而是综合利用这两类信息，为用户提供准确、有帮助、自然的回答。


============================================================
【用户问题】
============================================================

{question}


============================================================
【五经古典语料库检索结果】
============================================================

{context}


============================================================
【回答原则】
============================================================

1. 你可以正常使用自己的知识回答问题。

2. 五经语料库是你的重要参考资料，但不是你唯一的信息来源。

3. 如果语料库中存在与问题直接相关的内容：
   - 优先使用这些资料中的准确原文、法文翻译、典籍名称、章节、爻位等信息；
   - 可以结合你的知识进行解释、分析、补充和扩展。

4. 如果语料库中的资料不足：
   - 不要因此拒绝回答；
   - 可以使用你自己的知识继续回答；
   - 但必须明确区分哪些内容来自当前语料库，哪些属于你的通用知识。

5. 如果你引用了语料库中的中文原文或法文翻译：
   - 必须忠实于提供的资料；
   - 不要擅自修改原文；
   - 不要编造语料库不存在的法文翻译。

6. 如果用户询问古籍原文：
   - 优先引用当前语料库中实际检索到的原文；
   - 如果语料库没有对应原文，可以根据你的知识回答，但要明确说明该内容不是当前语料库检索结果。

7. 如果问题涉及《易经》《尚书》《诗经》《礼记》《春秋》等经典的历史背景、思想体系、哲学意义、作者、成书过程、学术流派等，而当前语料库没有相关内容：
   - 可以使用你的通用知识回答；
   - 不要说“因为语料库没有，所以无法回答”。

8. 对于需要解释、比较、分析的问题：
   - 不要只罗列资料；
   - 应该真正理解问题并进行分析。

9. 如果语料库资料与通用知识之间存在明显冲突：
   - 不要强行把两者混在一起；
   - 应明确指出“当前语料库记录为……”
   - 然后说明“通行资料通常认为……”
   - 让用户知道信息来源不同。

10. 回答应该自然、清晰、准确。
    不要每次都机械地说“根据语料库……”。

11. 如果用户的问题非常简单，直接回答即可。
    不需要为了体现 RAG 而强行加入大量语料库说明。

12. 不要虚构不存在的资料、文献、原文或法文翻译。

============================================================
【关于语料库来源的标注】
============================================================

当确实使用了语料库资料时，可以自然地使用：

“根据当前五经古典语料库……”

或者：

“在当前语料库中，该句记录为……”

如果回答主要来自你的通用知识，则可以说明：

“从通行的学术认识来看……”

如果两者结合：

“当前语料库收录的原文是……；从通行的易学解释来看……”

不要把 AI 自身知识伪装成语料库内容。


============================================================
【最终目标】
============================================================

你不是一个“只能查数据库”的机器人。

你是一个真正的智能学习助手：

- 能理解用户问题；
- 能检索五经语料库；
- 能利用自身知识；
- 能进行分析和推理；
- 能解释古籍；
- 能处理中法双语资料；
- 能比较不同经典；
- 能在资料不足时主动补充；
- 同时能够诚实地区分信息来源。


现在，请直接回答用户的问题。
"""


        else:

            # =================================================
            # 没有检索结果时
            #
            # 这是非常重要的改变：
            #
            # 以前：
            #     没有 RAG → 告诉用户“语料库没有，所以不能回答”
            #
            # 现在：
            #     没有 RAG → 正常调用千问自身知识回答
            # =================================================

            prompt = f"""
你是“五经古典语料库”的智能 AI 学习助手。

用户提出的问题是：

============================================================
{question}
============================================================


本次查询已经尝试检索当前五经古典语料库，但没有找到足够明确的匹配资料。


但是：

【这并不意味着你不能回答问题。】

你可以充分使用你自身已经具备的：

- 通用知识
- 古典文献知识
- 历史知识
- 哲学知识
- 语言理解能力
- 推理与分析能力


为用户提供正常、完整、有帮助的回答。


============================================================
【重要要求】
============================================================

1. 不要因为语料库没有检索到结果，就拒绝回答。

2. 可以直接使用你的通用知识回答。

3. 如果涉及五经、《易经》《尚书》《诗经》《礼记》《春秋》等经典，
   应尽可能提供准确、清晰的学术性说明。

4. 如果引用具体古籍原文，请尽量保证准确。

5. 不要声称这些内容来自当前五经语料库，因为本次检索没有找到对应资料。

6. 可以自然地告诉用户：

   “本次回答主要依据通用知识，因为当前语料库没有检索到直接相关资料。”

7. 如果用户的问题本身并不需要五经语料库，例如：
   - 一般知识问题
   - 历史问题
   - 哲学问题
   - 学习方法
   - 编程问题
   - 日常问题

   都应该正常回答，而不是要求用户先扩充语料库。

8. 回答要真正解决用户的问题，而不是只告诉用户“语料库没有资料”。


============================================================
【最终目标】
============================================================

你是一个真正的 AI 智能学习助手。

五经语料库只是你的一个专业知识来源，
而不是限制你的知识边界。

现在，请直接回答用户的问题。
"""


        # ====================================================
        # 第五步：调用通义千问
        # ====================================================

        print("正在请求通义千问……")


        answer = ask_qwen(prompt)


        print("✓ AI 回答生成成功")


        print()
        print("AI 回答：")
        print("-" * 70)
        print(answer)
        print("-" * 70)


        # ====================================================
        # 第六步：返回前端
        # ====================================================

        return jsonify({

            "success": True,

            "question": question,

            "answer": answer,

            "results": results

        })


    except Exception as e:

        # ====================================================
        # 异常处理
        # ====================================================

        print()
        print("❌ AI 服务出现异常：")
        print(e)


        return jsonify({

            "success": False,

            "error": str(e)

        }), 500



# ============================================================
# 语料库扩充接口
# ============================================================

@app.route("/api/corpus/auth", methods=["POST"])
def corpus_auth():

    admin_token = os.environ.get("CORPUS_ADMIN_TOKEN", "")
    request_token = request.headers.get("X-Corpus-Token", "")

    if not admin_token:
        return jsonify({
            "success": False,
            "error": "服务器未配置语料库管理员 Token"
        }), 500

    if request_token != admin_token:
        return jsonify({
            "success": False,
            "error": "管理员 Token 无效"
        }), 403

    return jsonify({
        "success": True,
        "message": "管理员验证成功"
    })


@app.route("/api/corpus/add", methods=["POST"])
def add_corpus():

    try:

        # ====================================================
        # 第一步：验证管理员 Token
        # ====================================================

        admin_token = os.environ.get(
            "CORPUS_ADMIN_TOKEN",
            ""
        )

        request_token = request.headers.get(
            "X-Corpus-Token",
            ""
        )

        if not admin_token:
            return jsonify({
                "success": False,
                "error": "服务器未配置语料库管理员 Token"
            }), 500

        if request_token != admin_token:
            return jsonify({
                "success": False,
                "error": "管理员 Token 无效"
            }), 403


        # ====================================================
        # 第二步：获取请求数据
        # ====================================================

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "没有收到语料数据"
            }), 400


        # ====================================================
        # 第三步：检查必填字段
        # ====================================================

        required_fields = [
            "book",
            "chapter",
            "chinese",
            "french"
        ]

        for field in required_fields:

            value = str(
                data.get(field, "") or ""
            ).strip()

            if not value:
                return jsonify({
                    "success": False,
                    "error": f"字段不能为空：{field}"
                }), 400


        # ====================================================
        # 第四步：读取 custom_corpus.json
        # ====================================================

        custom_file = os.path.join(BASE_DIR, "custom_corpus.json")

        if os.path.exists(custom_file):

            with open(
                custom_file,
                "r",
                encoding="utf-8"
            ) as f:

                corpus = json.load(f)

        else:

            corpus = []


        if not isinstance(corpus, list):

            return jsonify({
                "success": False,
                "error": "custom_corpus.json 格式错误"
            }), 500


        # ====================================================
        # 第五步：整理新语料
        # ====================================================

        new_record = {

            "corpus": data.get(
                "corpus",
                "自定义语料"
            ),

            "book": data.get(
                "book",
                ""
            ).strip(),

            "chapter": data.get(
                "chapter",
                ""
            ).strip(),

            "chinese": data.get(
                "chinese",
                ""
            ).strip(),

            "french": data.get(
                "french",
                ""
            ).strip(),

            "source": data.get(
                "source",
                "管理员添加"
            ).strip(),

            "meta": {

                "translator": data.get(
                    "translator",
                    ""
                ).strip(),

                "edition": data.get(
                    "edition",
                    ""
                ).strip(),

                "language": data.get(
                    "language",
                    "fr"
                ).strip()

            }

        }


        # ====================================================
        # 第六步：写入语料库
        # ====================================================

        corpus.append(new_record)

        with open(
            custom_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                corpus,
                f,
                ensure_ascii=False,
                indent=2
            )


        print()
        print("=" * 70)
        print("✓ 新语料添加成功")
        print(f"  典籍：{new_record['book']}")
        print(f"  篇章：{new_record['chapter']}")
        print("=" * 70)


        return jsonify({

            "success": True,

            "message": "语料添加成功",

            "record": new_record,

            "total": len(corpus)

        })


    except Exception as e:

        print()
        print("❌ 语料添加失败：")
        print(e)

        return jsonify({

            "success": False,

            "error": str(e)

        }), 500


# ============================================================
# 启动服务器
# ============================================================

@app.route("/api/corpus/import", methods=["POST"])
def import_corpus():

    try:

        # ====================================================
        # 第一步：验证管理员 Token
        # ====================================================

        admin_token = os.environ.get(
            "CORPUS_ADMIN_TOKEN",
            ""
        )

        request_token = request.headers.get(
            "X-Corpus-Token",
            ""
        )

        if not admin_token:
            return jsonify({
                "success": False,
                "error": "服务器未配置语料库管理员 Token"
            }), 500

        if request_token != admin_token:
            return jsonify({
                "success": False,
                "error": "管理员 Token 无效"
            }), 403

        # ====================================================
        # 第二步：获取上传文件
        # ====================================================

        uploaded_file = request.files.get("file")

        if not uploaded_file:
            return jsonify({
                "success": False,
                "error": "没有收到上传文件"
            }), 400

        filename = uploaded_file.filename or ""
        extension = os.path.splitext(filename)[1].lower()

        if extension not in [".xlsx", ".xls", ".csv", ".json"]:
            return jsonify({
                "success": False,
                "error": "只支持 Excel、CSV、JSON 文件"
            }), 400

        # ====================================================
        # 第三步：读取文件
        # ====================================================

        records = []

        if extension in [".xlsx", ".xls"]:

            workbook = openpyxl.load_workbook(
                uploaded_file,
                read_only=True,
                data_only=True
            )

            sheet = workbook.active
            rows = list(sheet.iter_rows(values_only=True))

            if not rows:
                return jsonify({
                    "success": False,
                    "error": "Excel 文件为空"
                }), 400

            headers = [
                str(value).strip() if value is not None else ""
                for value in rows[0]
            ]

            for row in rows[1:]:

                record = {}

                for index, value in enumerate(row):

                    if index < len(headers) and headers[index]:
                        record[headers[index]] = (
                            str(value).strip()
                            if value is not None
                            else ""
                        )

                if any(record.values()):
                    records.append(record)

            workbook.close()

        elif extension == ".csv":

            content = uploaded_file.read().decode(
                "utf-8-sig"
            )

            reader = csv.DictReader(
                io.StringIO(content)
            )

            for row in reader:

                record = {}

                for key, value in row.items():

                    key = (
                        str(key).strip()
                        if key is not None
                        else ""
                    )

                    value = (
                        str(value).strip()
                        if value is not None
                        else ""
                    )

                    if key:
                        record[key] = value

                if any(record.values()):
                    records.append(record)

        elif extension == ".json":

            content = uploaded_file.read().decode(
                "utf-8-sig"
            )

            data = json.loads(content)

            if isinstance(data, list):

                records = data

            elif isinstance(data, dict):

                if isinstance(data.get("records"), list):
                    records = data["records"]

                elif isinstance(data.get("data"), list):
                    records = data["data"]

                else:
                    records = [data]

            else:

                return jsonify({
                    "success": False,
                    "error": "JSON 文件格式不正确"
                }), 400

        # ====================================================
        # 第四步：检查数据
        # ====================================================

        required_fields = [
            "book",
            "chapter",
            "chinese",
            "french"
        ]

        valid_records = []
        skipped_records = []

        for index, data in enumerate(records, 1):

            if not isinstance(data, dict):
                skipped_records.append({
                    "row": index,
                    "reason": "不是有效的数据对象"
                })
                continue

            missing_fields = []

            for field in required_fields:

                value = str(
                    data.get(field, "") or ""
                ).strip()

                if not value:
                    missing_fields.append(field)

            if missing_fields:

                skipped_records.append({
                    "row": index,
                    "reason": (
                        "缺少字段："
                        + "、".join(missing_fields)
                    )
                })

                continue

            new_record = {
                "corpus": str(
                    data.get(
                        "corpus",
                        "自定义语料"
                    ) or "自定义语料"
                ).strip(),

                "book": str(
                    data.get("book", "") or ""
                ).strip(),

                "chapter": str(
                    data.get("chapter", "") or ""
                ).strip(),

                "chinese": str(
                    data.get("chinese", "") or ""
                ).strip(),

                "french": str(
                    data.get("french", "") or ""
                ).strip(),

                "source": str(
                    data.get(
                        "source",
                        "批量导入"
                    ) or "批量导入"
                ).strip(),

                "meta": {
                    "translator": str(
                        data.get(
                            "translator",
                            ""
                        ) or ""
                    ).strip(),

                    "edition": str(
                        data.get(
                            "edition",
                            ""
                        ) or ""
                    ).strip(),

                    "language": str(
                        data.get(
                            "language",
                            "fr"
                        ) or "fr"
                    ).strip()
                }
            }

            valid_records.append(new_record)

        if not valid_records:

            return jsonify({
                "success": False,
                "error": "没有找到有效语料",
                "total_rows": len(records),
                "skipped": skipped_records
            }), 400

        # ====================================================
        # 第五步：读取现有自定义语料
        # ====================================================

        custom_file = os.path.join(
            BASE_DIR,
            "custom_corpus.json"
        )

        if os.path.exists(custom_file):

            with open(
                custom_file,
                "r",
                encoding="utf-8"
            ) as f:

                corpus = json.load(f)

        else:

            corpus = []

        if not isinstance(corpus, list):

            return jsonify({
                "success": False,
                "error": "custom_corpus.json 格式错误"
            }), 500

        # ====================================================
        # 第六步：批量写入
        # ====================================================

        corpus.extend(valid_records)

        with open(
            custom_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                corpus,
                f,
                ensure_ascii=False,
                indent=2
            )

        print()
        print("=" * 70)
        print("✓ 批量语料导入成功")
        print(f"  文件：{filename}")
        print(f"  成功：{len(valid_records)} 条")
        print(f"  跳过：{len(skipped_records)} 条")
        print(f"  自定义语料总数：{len(corpus)} 条")
        print("=" * 70)

        return jsonify({
            "success": True,
            "message": "批量语料导入成功",
            "filename": filename,
            "imported": len(valid_records),
            "skipped": len(skipped_records),
            "skipped_records": skipped_records,
            "total": len(corpus)
        })

    except Exception as error:

        print()
        print("✗ 批量语料导入失败：")
        print(error)

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


if __name__ == "__main__":

    print("=" * 60)
    print("五经古典语料库 AI 服务")
    print("=" * 60)

    print("正在启动服务器……")
    print()

    port = int(os.environ.get("PORT", 5001))

    print("浏览器测试地址：")
    print(f"http://127.0.0.1:{port}")

    print()

    print("AI API 地址：")
    print(f"http://127.0.0.1:{port}/api/ask")

    print()

    print("按 Ctrl + C 可以停止服务器")

    print("=" * 60)

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )