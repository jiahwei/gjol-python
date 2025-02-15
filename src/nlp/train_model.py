import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
import joblib
from pathlib import Path
from src.nlp.service import preprocess_text
from collections import Counter

def train():
    # 1. 加载数据集
    data_path = Path('data/paragraphs.csv')
    data = pd.read_csv(data_path)

    # 确保数据有 'paragraph' 和 'label' 两列
    if 'paragraph' not in data.columns or 'label' not in data.columns:
        raise ValueError("数据集应包含 'paragraph' 和 'label' 两列。")
    label_counts = Counter(data['label'])
    print("数据分布:")
    for label, count in label_counts.items():
        print(f"{label}: {count}")
    
    # 2. 文本预处理

    print("正在预处理文本...")
    data['processed_paragraph'] = data['paragraph'].apply(preprocess_text)

    # 3. 标签编码
    label_encoder = LabelEncoder()
    data['label_encoded'] = label_encoder.fit_transform(data['label'])

    # 4. 分割训练集和测试集
    X = data['processed_paragraph']
    y = data['label_encoded']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, stratify=y, random_state=42)

    # 5. 特征提取
    print("正在提取特征...")
    vectorizer = TfidfVectorizer()
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)

    # 6. 训练模型
    print("正在训练模型...")
    # model = MultinomialNB()
    # model.fit(X_train_tfidf, y_train)
    model = LogisticRegression(max_iter=1000, class_weight='balanced')
    model.fit(X_train_tfidf, y_train)


    # 7. 模型评估
    print("正在评估模型...")
    y_pred = model.predict(X_test_tfidf)
    # 获取实际的测试类别
    actual_classes = np.unique(y_test)
    target_names = label_encoder.inverse_transform(actual_classes)

    # 生成分类报告，指定 labels 参数
    report = classification_report(y_test, y_pred, labels=actual_classes, target_names=target_names)
    print(report)

    # 8. 保存模型和相关对象
    models_dir = Path('src/nlp/models')

    joblib.dump(model, models_dir.joinpath('paragraph_classifier.model'))
    print("模型已保存至 'models/paragraph_classifier.model'")

    joblib.dump(vectorizer, models_dir.joinpath('tfidf_vectorizer.model'))
    print("向量器已保存至 'models/tfidf_vectorizer.model'")

    joblib.dump(label_encoder, models_dir.joinpath('label_encoder.model'))
    print("标签编码器已保存至 'models/label_encoder.model'")