import logging
import re,json
from pathlib import Path
from typing import Set

import joblib
import thulac
from bs4 import BeautifulSoup, Tag


from src.bulletin.models import BulletinDB
from src.bulletin.schemas import ContentTotal,ParagraphTopic
from src.bulletin_list.schemas import BulletinType, DownloadBulletin
from src.spiders.service import get_base_bulletin

logger = logging.getLogger("nlp_test")
thu1 = thulac.thulac(user_dict=Path("src/nlp/user_dict.txt"), filt=False, seg_only=True)
# 加载模型、向量器、标签编码器
models_dir = Path("src/nlp/models")
model = joblib.load(models_dir.joinpath("paragraph_classifier.model"))
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


def load_stopwords() -> Set[str]:
    stopwords = set()
    stopwords_path = Path("src/nlp/cn_stopwords.txt")
    with open(stopwords_path, "r", encoding="utf-8") as f:
        for line in f:
            stopwords.add(line.strip())
    return stopwords


def predict_paragraph_category(paragraph_text: str) -> str:
    # 转换为特征向量
    X_new = vectorizer.transform([paragraph_text])
    # 进行预测
    prediction = model.predict(X_new)
    # 解码标签
    label = label_encoder.inverse_transform(prediction)
    return label[0]


def nlp_test(
    content_path: Path | None, bulletin_info: DownloadBulletin
) -> BulletinDB | None:
    if content_path is None:
        logger.warning("content_path is None")
        return None
    logger.info(
        f"处理{content_path}",
    )
    base_bulletin = get_base_bulletin(content_path, bulletin_info)
    content = content_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(content, "html5lib")
    details_div = soup.find("div", class_="details")
    if not isinstance(details_div, Tag):
        logger.warning("details_div为空，规则失效")
        return base_bulletin
    paragraphs = details_div.find_all("p")
    
    # 按类型分组段落
    category_contents = {}  # 类型 -> 内容列表
    category_lengths = {}   # 类型 -> 总长度
    
    for p in paragraphs:
        p_text = p.text
        words = preprocess_text(p_text)
        if words.strip():
            category = predict_paragraph_category(words)
            logger.info(f"{p_text},段落类型：{category}")
            
            # 将段落添加到对应类型
            if category not in category_contents:
                category_contents[category] = []
                category_lengths[category] = 0
            
            category_contents[category].append(p_text)
            category_lengths[category] += len(p_text)
    

    content_total_arr:list[ContentTotal] = []
    for category, contents in category_contents.items():
        content_item = ContentTotal(
            type=ParagraphTopic(category),
            leng=category_lengths[category],
            content=contents
        )
        content_total_arr.append(content_item)
    
    # 直接序列化对象，Pydantic 会自动处理枚举值
    content_total_json = json.dumps([item.model_dump() for item in content_total_arr], ensure_ascii=False)
    base_bulletin.content_total_arr = content_total_json

    return base_bulletin
