"""
自然语言处理服务模块
"""
import json
import functools
import logging
import re
from pathlib import Path

import joblib
import requests
import thulac

from src.bulletin.schemas import ParagraphTopic

# from src.spiders.service import get_base_bulletin

logger = logging.getLogger("nlp_test")
thu1 = thulac.thulac(user_dict=Path("src/nlp/user_dict.txt"), filt=False, seg_only=True)
# 加载模型、向量器、标签编码器
models_dir = Path("src/nlp/models")
# model = joblib.load(models_dir.joinpath("paragraph_classifier.model"))
model = joblib.load(models_dir.joinpath("ensemble_classifier.model"))
vectorizer = joblib.load(models_dir.joinpath("tfidf_vectorizer.model"))
label_encoder = joblib.load(models_dir.joinpath("label_encoder.model"))


def preprocess_text(text: str) -> str:
    """
    预处理输入文本，执行以下步骤：
    1. 将多个空白字符替换为一个空格。
    2. 移除所有非字母数字字符（空白字符除外）。
    3. 去除首尾空白字符。
    4. 使用THULAC进行分词和词性标注。
    5. 从分词结果中移除停用词。

    参数:
        text (str): 要预处理的输入文本。

    返回:
        str: 预处理后的文本，停用词被移除，单词用空格连接。
    """
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s]", "", text)
    text = text.strip()
    words_tags = thu1.cut(text, text=False)
    words = [word for word, tag in words_tags]
    stopwords = load_stopwords()
    words = [word for word in words if word.strip() and word not in stopwords]
    return " ".join(words)


def load_stopwords() -> set[str]:
    """
    从文件中加载停用词。

    返回:
        set[str]: 包含停用词的集合。
    """
    stopwords = set()
    stopwords_path = Path("src/nlp/cn_stopwords.txt")
    with open(stopwords_path, "r", encoding="utf-8") as f:
        for line in f:
            stopwords.add(line.strip())
    return stopwords


def predict_paragraph_category(paragraph_text: str) -> str:
    """
    预测段落的类别。

    参数:
        paragraph_text (str): 要预测的段落文本。

    返回:
        str: 预测的段落类别。
    """
    # "无更新" 模式训练量太小，直接判断返回
    if "无更新" in paragraph_text:
        return "无更新"
    # 转换为特征向量
    x_new = vectorizer.transform([paragraph_text])
    # 进行预测
    prediction = model.predict(x_new)
    # 解码标签
    label = label_encoder.inverse_transform(prediction)
    return label[0]

# Ollama 模型配置 ，只有本地显卡算力，服务器上使用传统分类模型去预测
_OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"
_OLLAMA_MODEL = "deepseek-r1:14b"
_OLLAMA_PROMPT_PATH = Path("src/nlp/ollama_paragraph_category_prompt.txt")


@functools.lru_cache(maxsize=1)
def _get_ollama_prompt_template() -> str:
    return _OLLAMA_PROMPT_PATH.read_text(encoding="utf-8")


def _format_indexed_paragraphs(paragraphs: list[str]) -> str:
    return "\n".join(f"[{i}] {p}" for i, p in enumerate(paragraphs))


def _build_ollama_category_prompt(paragraphs: list[str], categories: list[str]) -> str:
    template = _get_ollama_prompt_template()
    return template.format(
        categories=", ".join(categories),
        paragraphs_text=_format_indexed_paragraphs(paragraphs),
    )


def _strip_think_tags(text: str) -> str:
    if "</think>" in text:
        return text.split("</think>")[-1].strip()
    return text


def _ollama_generate(prompt: str) -> str | None:
    payload = {
        "model": _OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "top_p": 0.1,
            "repeat_penalty": 1.1,
            "max_tokens": 1024,
        },
    }

    try:
        response = requests.post(_OLLAMA_GENERATE_URL, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
    except requests.RequestException as e:
        logger.error("请求 Ollama 服务失败: %s", str(e))
        return None
    except json.JSONDecodeError as e:
        logger.error("解析 Ollama 响应 JSON 失败: %s", str(e))
        return None

    prediction = str(result.get("response", "")).strip()
    return _strip_think_tags(prediction)


def _match_category(cat_text: str, categories: list[str], default: str = "格式") -> str:
    for c in categories:
        if c in cat_text:
            return c
    return default


def _parse_indexed_categories(prediction: str, categories: list[str]) -> dict[int, str]:
    category_map: dict[int, str] = {}
    for raw_line in prediction.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = re.match(r"\[(\d+)\]\s*(.*)", line)
        if not match:
            continue
        idx = int(match.group(1))
        category_map[idx] = _match_category(match.group(2), categories)
    return category_map


def _fallback_categories(paragraphs: list[str]) -> list[str]:
    return [predict_paragraph_category(preprocess_text(p)) for p in paragraphs]


def _fill_missing_categories(paragraphs: list[str], category_map: dict[int, str]) -> list[str]:
    final_categories: list[str] = []
    last_cat: str | None = None
    for i, paragraph in enumerate(paragraphs):
        cat = category_map.get(i)
        if cat is None:
            cat = last_cat or predict_paragraph_category(preprocess_text(paragraph))
        else:
            last_cat = cat
        final_categories.append(cat)
    return final_categories


def predict_paragraphs_category_ollama(paragraphs: list[str]) -> list[str]:
    """
    使用本地 Ollama 模型批量预测段落的类别，利用上下文（小标题）提高准确率。

    参数:
        paragraphs (list[str]): 要预测的段落文本列表。

    返回:
        list[str]: 预测的段落类别列表，与输入列表一一对应。
    """
    if not paragraphs:
        return []

    categories = [topic.value for topic in ParagraphTopic]
    prompt = _build_ollama_category_prompt(paragraphs, categories)
    prediction = _ollama_generate(prompt)
    if not prediction:
        return _fallback_categories(paragraphs)

    category_map = _parse_indexed_categories(prediction, categories)
    return _fill_missing_categories(paragraphs, category_map)
