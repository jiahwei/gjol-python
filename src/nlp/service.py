import thulac,re,logging
from pathlib import Path
from bs4 import BeautifulSoup, Tag
from typing import Set, Union, List, Optional
import joblib


from src.bulletin_list.schemas import BulletinType
from src.bulletin.models import Bulletin
from src.bulletin_list.schemas import DownloadBulletin
from src.spiders.service import get_base_bulletin
from constants import DEFAULT_SQLITE_PATH, BASEURL, DEFAULT_FLODER_PATH_ABSOLUTE


logger = logging.getLogger('nlp_test')
thu1 = thulac.thulac(user_dict=Path('src/nlp/user_dict.txt'),filt=False,seg_only=True)
# 加载模型、向量器、标签编码器
models_dir = Path('src/nlp/models')
model = joblib.load(models_dir.joinpath('paragraph_classifier.model'))
vectorizer = joblib.load(models_dir.joinpath('tfidf_vectorizer.model'))
label_encoder = joblib.load(models_dir.joinpath('label_encoder.model'))

def preprocess_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    text = text.strip()
    words_tags = thu1.cut(text, text=False)
    words = [word for word, tag in words_tags]
    stopwords = load_stopwords()
    words = [word for word in words if word.strip() and word not in stopwords]
    return ' '.join(words)


def load_stopwords() -> Set[str]:
    stopwords = set()
    stopwords_path = Path('src/nlp/cn_stopwords.txt')
    with open(stopwords_path, 'r', encoding='utf-8') as f:
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
    content_path: Optional[Path], bulletin_info: DownloadBulletin
) -> Bulletin | None:
    if content_path is None:
        logger.warning("content_path is None")
        return None
    logger.info(f"处理{content_path}",)
    base_bulletin = get_base_bulletin(content_path, bulletin_info)
    content = content_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(content, "html5lib")
    details_div = soup.find("div", class_="details")
    if not isinstance(details_div, Tag):
        logger.warning("details_div为空，规则失效")
        return base_bulletin
    paragraphs = details_div.find_all("p")
    for p in paragraphs:
        p_text = p.text
        words = preprocess_text(p_text)
        # logger.info(f"分词：{words}")
        category = predict_paragraph_category(words)
        logger.info(f"{p_text},类别：{category}")
    return base_bulletin


