"""Natural language processing helpers for bulletin paragraph classification."""

import functools
import logging
import os
import re
from pathlib import Path

import joblib
import requests
import thulac
from dotenv import load_dotenv

from src.bulletin.schemas import ParagraphTopic

logger = logging.getLogger("nlp_test")

_ = load_dotenv()

thu1 = thulac.thulac(
    user_dict=Path("src/nlp/user_dict.txt"),
    filt=False,
    seg_only=True,
)

models_dir = Path("src/nlp/models")
model = joblib.load(models_dir.joinpath("ensemble_classifier.model"))
vectorizer = joblib.load(models_dir.joinpath("tfidf_vectorizer.model"))
label_encoder = joblib.load(models_dir.joinpath("label_encoder.model"))

LM_STUDIO_BASE_URL = os.getenv("LM_STUDIO_BASE_URL", "http://127.0.0.1:1234")
LM_STUDIO_CHAT_URL = f"{LM_STUDIO_BASE_URL.rstrip('/')}/api/v1/chat"
LM_STUDIO_MODELS_URL = f"{LM_STUDIO_BASE_URL.rstrip('/')}/api/v1/models"
LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "").strip()
LM_STUDIO_PROMPT_PATH = Path("src/nlp/lm_studio_paragraph_category_prompt.txt")


def preprocess_text(text: str) -> str:
    """Normalize text, tokenize with THULAC, and remove stopwords."""
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s]", "", text)
    text = text.strip()
    words_tags = thu1.cut(text, text=False)
    words = [word for word, _tag in words_tags]
    stopwords = load_stopwords()
    words = [word for word in words if word.strip() and word not in stopwords]
    return " ".join(words)


def load_stopwords() -> set[str]:
    """Load Chinese stopwords from disk."""
    stopwords = set()
    stopwords_path = Path("src/nlp/cn_stopwords.txt")
    with open(stopwords_path, "r", encoding="utf-8") as f:
        for line in f:
            stopwords.add(line.strip())
    return stopwords


def predict_paragraph_category(paragraph_text: str) -> str:
    """Predict a paragraph category with the traditional classifier."""
    if "无更新" in paragraph_text:
        return "无更新"

    x_new = vectorizer.transform([paragraph_text])
    prediction = model.predict(x_new)
    label = label_encoder.inverse_transform(prediction)
    return label[0]


@functools.lru_cache(maxsize=1)
def _get_lm_studio_prompt_template() -> str:
    return LM_STUDIO_PROMPT_PATH.read_text(encoding="utf-8")


def _format_indexed_paragraphs(paragraphs: list[str]) -> str:
    return "\n".join(f"[{i}] {paragraph}" for i, paragraph in enumerate(paragraphs))


def _build_lm_studio_category_prompt(paragraphs: list[str], categories: list[str]) -> str:
    template = _get_lm_studio_prompt_template()
    return template.format(
        categories=", ".join(categories),
        paragraphs_text=_format_indexed_paragraphs(paragraphs),
    )


def _strip_think_tags(text: str) -> str:
    if "</think>" in text:
        return text.split("</think>")[-1].strip()
    return text


@functools.lru_cache(maxsize=1)
def _get_lm_studio_model() -> str | None:
    if LM_STUDIO_MODEL:
        logger.info("Using LM Studio model from environment: %s", LM_STUDIO_MODEL)
        return LM_STUDIO_MODEL

    try:
        response = requests.get(LM_STUDIO_MODELS_URL, timeout=30)
        response.raise_for_status()
        result = response.json()
    except requests.RequestException as exc:
        logger.error("Requesting LM Studio models failed: %s", exc)
        return None
    except ValueError as exc:
        logger.error("Parsing LM Studio models response failed: %s", exc)
        return None

    models = result.get("models", [])
    for model_info in models:
        if model_info.get("type") != "llm":
            continue
        model_key = model_info.get("key")
        if isinstance(model_key, str) and model_key.strip():
            logger.info("Using first available LM Studio model: %s", model_key.strip())
            return model_key.strip()

    logger.error("No available LLM model was found from LM Studio /api/v1/models")
    return None


def _lm_studio_generate(prompt: str) -> str | None:
    model_name = _get_lm_studio_model()
    if not model_name:
        return None

    payload = {
        "model": model_name,
        "input": prompt,
        "stream": False,
        "temperature": 0.0,
        "top_p": 0.1,
        "repeat_penalty": 1.1,
        "max_output_tokens": 1024,
        "store": False,
    }

    try:
        response = requests.post(LM_STUDIO_CHAT_URL, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
    except requests.RequestException as exc:
        logger.error("Requesting LM Studio chat failed: %s", exc)
        return None
    except ValueError as exc:
        logger.error("Parsing LM Studio chat response failed: %s", exc)
        return None

    output = result.get("output", [])
    message_parts: list[str] = []
    for item in output:
        if item.get("type") != "message":
            continue
        content = item.get("content")
        if isinstance(content, str) and content.strip():
            message_parts.append(content.strip())

    prediction = "\n".join(message_parts).strip()
    if not prediction:
        logger.error("LM Studio response did not contain any usable message content")
        return None

    return _strip_think_tags(prediction)


def _match_category(cat_text: str, categories: list[str], default: str = "格式") -> str:
    for category in categories:
        if category in cat_text:
            return category
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
    return [predict_paragraph_category(preprocess_text(paragraph)) for paragraph in paragraphs]


def _fill_missing_categories(paragraphs: list[str], category_map: dict[int, str]) -> list[str]:
    final_categories: list[str] = []
    last_category: str | None = None
    for index, paragraph in enumerate(paragraphs):
        category = category_map.get(index)
        if category is None:
            category = last_category or predict_paragraph_category(preprocess_text(paragraph))
        else:
            last_category = category
        final_categories.append(category)
    return final_categories


def predict_paragraphs_category_lm_studio(paragraphs: list[str]) -> list[str]:
    """Predict paragraph categories with LM Studio and keep the old ML model as fallback."""
    if not paragraphs:
        return []

    categories = [topic.value for topic in ParagraphTopic]
    prompt = _build_lm_studio_category_prompt(paragraphs, categories)
    prediction = _lm_studio_generate(prompt)
    if not prediction:
        return _fallback_categories(paragraphs)

    category_map = _parse_indexed_categories(prediction, categories)
    return _fill_missing_categories(paragraphs, category_map)
