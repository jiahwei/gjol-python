# pyright: reportMissingTypeStubs=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownMemberType=false
import logging
import re
from pathlib import Path

import joblib
import thulac

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
    # 转换为特征向量
    x_new = vectorizer.transform([paragraph_text])
    # 进行预测
    prediction = model.predict(x_new)
    # 解码标签
    label = label_encoder.inverse_transform(prediction)
    return label[0]
