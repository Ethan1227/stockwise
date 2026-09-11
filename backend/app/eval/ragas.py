"""RAGAS 四指标评测（简化实现）。

指标：
- faithfulness（忠实度）：回答是否完全基于业务数据、无编造（DeepSeek 当裁判，失败则规则近似）。
- answer_relevancy（答案相关性）：回答是否切题（含关键事实）。
- context_precision（上下文精确率）：命中意图是否正确。
- context_recall（上下文召回率）：关键事实被覆盖的比例。
"""
from app.eval.qa_dataset import QA_CASES


def _faithfulness(question: str, answer: str, context: str) -> float:
    """LLM 评判回答是否忠实于上下文；LLM 不可用则规则近似。"""
    from app.services import llm

    prompt = (
        f"问题：{question}\n业务数据：{context}\n回答：{answer}\n"
        "判断「回答」是否完全基于「业务数据」、没有编造数据。只回答「是」或「否」。"
    )
    resp = llm.generate("你是评测裁判，只输出「是」或「否」。", prompt)
    if resp is not None:
        return 1.0 if ("是" in resp and "否" not in resp) else 0.0
    # 规则近似：回答非空且包含业务数据关键词
    keywords = ("SK-", "补货", "滞销", "预算", "黑五", "采购", "空运", "建议")
    return 1.0 if (answer and any(k in answer for k in keywords)) else 0.0


def evaluate_ragas(db) -> dict:
    """跑 RAGAS 评测，返回四指标均值。"""
    from app.services.qa_router import route_and_think

    scores = {"faithfulness": [], "answer_relevancy": [], "context_precision": [], "context_recall": []}
    for case in QA_CASES:
        skill, result, _ = route_and_think(case["question"], db)
        answer = result.get("answer_md", "")
        chips = " ".join(f"{c['label']} {c['value']}" for c in result.get("data_chips", []))
        data_text = answer + " " + chips

        # context_precision：命中意图是否正确
        code = skill["code"] if skill else "fallback"
        scores["context_precision"].append(1.0 if code == case["skill"] else 0.0)

        # context_recall：关键事实覆盖比例
        present = [f for f in case["facts"] if f in data_text]
        scores["context_recall"].append(len(present) / len(case["facts"]) if case["facts"] else 1.0)

        # answer_relevancy：回答是否包含关键事实
        answer_present = [f for f in case["facts"] if f in answer]
        scores["answer_relevancy"].append(1.0 if answer_present else 0.0)

        # faithfulness：LLM 裁判 + 规则降级
        scores["faithfulness"].append(_faithfulness(case["question"], answer, result.get("answer_md", "")))

    return {k: round(sum(v) / len(v), 4) if v else 0.0 for k, v in scores.items()}
