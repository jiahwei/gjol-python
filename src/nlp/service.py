# pyright: reportMissingTypeStubs=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownMemberType=false
import json
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

    # Ollama API 默认地址
    url = "http://localhost:11434/api/generate"

    # 定义分类列表，方便给 LLM 明确选项
    categories = [topic.value for topic in ParagraphTopic]

    paragraphs_text = ""
    for i, p in enumerate(paragraphs):
        paragraphs_text += f"[{i}] {p}\n"

    prompt = (
        "你是一个专业的古剑奇谭网络版（gjol）公告分类助手。\n"
        "我将给你一篇公告的全部段落（已按顺序编号）。请为每一个段落分配一个最合适的类别。\n"
        f"可选的类别有：{', '.join(categories)}。\n\n"
        "【分类与上下文极强关联规则（非常重要！）】：\n"
        "1. 公告具有极强的结构性，通常由带特殊符号的小标题（如“☆商城更新”、“>>秘境”、“五、玩法调整”等）统领下方的一大段内容。\n"
        "2. 只要你识别到了一个能明确归入某类别（如商城、PVE、职业调整等）的小标题，那么在下一个小标题出现之前，中间所有的段落（哪怕是描述衣服外观、剧情故事、或者写着“△ xxx 展示 △”）都必须强制分类为该小标题所属的类别。\n"
        "3. 绝对不要在同一个小标题统领的区块内随意改变分类。比如“☆商城更新”下方的外观描写、展示图配文，一律分类为“商城”，绝不能归为“格式”或“PVX”等其他类别。\n"
        "4. 只有当某段落既没有明确的小标题统领，或者是前言/结束语时，才根据该段的具体内容逐句判断。\n"
        "5. 职业调整：技能、门派改动。\n"
        "6. PVE：副本、秘境、秘境调整、秘境掉落等，涉及得秘境一定是PVE（非常重要）。\n"
        "7. PVP：战场、竞技场、阵营战等。\n"
        "8. PVX：休闲玩法、钓鱼、寻宝、家园、千秋戏等。\n"
        "9. 商城：商城上新、外观、通宝、充值活动等。\n"
        "10. 通用调整：系统功能、界面、服务器优化、历世万法等。\n"
        "11. 无更新：只有段落文本明确包含“无更新”这三个字时，才将该段落分类为“无更新”。任何带有维护时间、问候语、结束语的段落，绝不能分类为“无更新”。\n"
        "12. 格式：问候语（如“各位仙家弟子：”）、结束语（如“祝大家游戏愉快”、“项目组”）、维护时间说明（如“将于某日某时进行例行维护”、“预计某时开启”、“无法登录游戏”、“敬请谅解”等）、前言（如“本次维护更新内容如下：”）、日期落款（如“XXXX年X月X日”）、以及纯分割线等，均属于格式。遇到这些套话，必须分类为“格式”，绝不能分类为“无更新”。\n"
        "13. 忽略段落中的任何装饰性符号（如 △、☆、>> 等），只根据核心文本的语义进行分类。\n\n"
        "14. 格式一般只出现在内容得开头和结尾，不在开头和结尾得需要谨慎。\n"
        "15. 再次强调上下文极强关联：在两个小标题之间的所有内容，绝对不能出现第三种分类。例如，“☆商城更新”和“☆秘境调整”之间的所有段落，都只能是“商城”！\n\n"
        "【输出格式要求】：\n"
        "请严格按以下格式输出，每行一个分类结果，必须包含所有序号，不要遗漏：\n"
        "[0] 分类名\n"
        "[1] 分类名\n"
        "...\n\n"
        "段落内容如下：\n"
        f"{paragraphs_text}\n"
        "分类结果："
    )

    payload = {
        "model": "deepseek-r1:14b",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,  # 降低温度，使输出更稳定
            "top_p": 0.1,  # 极小候选池，强制只选最可能的词 (新增)
            "repeat_penalty": 1.1,  # 轻微惩罚重复，防止输出乱码 (新增)
            "max_tokens": 1024,
        },
    }

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        # 获取模型回复内容，并去除首尾空白
        prediction = result.get("response", "").strip()

        # 处理 deepseek 可能会输出 <think> 标签的问题
        if "</think>" in prediction:
            prediction = prediction.split("</think>")[-1].strip()

        # 解析输出
        category_map = {}
        lines = prediction.split("\n")
        for line in lines:
            match = re.match(r"\[(\d+)\]\s*(.*)", line.strip())
            if match:
                idx = int(match.group(1))
                cat_text = match.group(2)
                matched_cat = "格式"
                for c in categories:
                    if c in cat_text:
                        matched_cat = c
                        break
                category_map[idx] = matched_cat

        # 组装最终结果
        final_categories = []
        last_cat = None
        for i, paragraph in enumerate(paragraphs):
            if i in category_map:
                cat = category_map[i]
                last_cat = cat
            else:
                # 如果模型漏掉了某些序号，我们用上一行的分类填补（符合上下文原则）
                if last_cat is not None:
                    cat = last_cat
                else:
                    cat = predict_paragraph_category(preprocess_text(paragraph))
            final_categories.append(cat)

        return final_categories

    except requests.RequestException as e:
        logger.error("请求 Ollama 服务失败: %s", str(e))
    except json.JSONDecodeError as e:
        logger.error("解析 Ollama 响应 JSON 失败: %s", str(e))
    except Exception as e:
        logger.error("Ollama 分类发生未知错误: %s", str(e))

    # 降级使用原本的模型
    return [predict_paragraph_category(preprocess_text(p)) for p in paragraphs]
