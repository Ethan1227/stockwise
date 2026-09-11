"""评测指标：accuracy / precision / recall / f1（macro 平均）。"""


def classification_metrics(y_true: list[str], y_pred: list[str]) -> dict:
    """计算分类指标（macro 平均），返回四指标 + 各类别明细。"""
    n = len(y_true)
    if n == 0:
        return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0, "samples": 0, "per_label": {}}

    labels = sorted(set(y_true) | set(y_pred))
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)

    per_label = {}
    precisions, recalls, f1s = [], [], []
    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        per_label[label] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": sum(1 for t in y_true if t == label),
        }
        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)

    return {
        "accuracy": round(correct / n, 4),
        "precision": round(sum(precisions) / len(precisions), 4),
        "recall": round(sum(recalls) / len(recalls), 4),
        "f1": round(sum(f1s) / len(f1s), 4),
        "samples": n,
        "per_label": per_label,
    }
