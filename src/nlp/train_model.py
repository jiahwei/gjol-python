# pyright: reportMissingTypeStubs=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownMemberType=false
# pyright: reportAny=false
import csv
import logging
import os
from collections import Counter
from logging import Logger
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from pandas import DataFrame
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier, VotingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from src.nlp.service import preprocess_text

train_logger: Logger = logging.getLogger("train")


def get_merge_csv_data() -> pd.DataFrame:
    """
    合并基础CSV数据和检查文件夹中的新数据

    Returns:
        DataFrame: 合并后的数据
    """
    base_csv: pd.DataFrame = pd.read_csv('data/paragraphs.csv')
    check_folder = 'data/check'
    all_files = [os.path.join(check_folder, f) for f in os.listdir(check_folder) if f.endswith('.csv')]

    if all_files:
        for file in all_files:
            new_data = pd.read_csv(file)
            base_csv = pd.concat([base_csv, new_data]).drop_duplicates().reset_index(drop=True)
        base_csv.to_csv('data/paragraphs_update.csv', index=False, quoting=csv.QUOTE_ALL)
        return pd.read_csv('data/paragraphs_update.csv')
    else:
        return base_csv


def replace_old_csv() -> None:
    """
    用更新后的CSV替换原始CSV文件
    """
    if not os.path.exists('data/paragraphs_update.csv'):
        print("paragraphs_update.csv 不存在，操作中止。")
        return
    os.replace('data/paragraphs_update.csv', 'data/paragraphs.csv')


def preprocess_data_with_context(data: DataFrame) -> DataFrame:
    """
    预处理数据，添加上下文特征

    Args:
        data: 原始数据

    Returns:
        DataFrame: 添加了上下文特征的数据
    """
    processed_data = data.copy()
    processed_data['is_title'] = processed_data['paragraph'].str.startswith('☆')
    processed_data['title_category'] = None
    current_title_category = None

    # 遍历数据，为每个段落添加其所属的标题类别
    for i, row in processed_data.iterrows():
        if row['is_title'] == True:
            # 如果是标题行，更新当前标题类别
            current_title_category = row['label']

        # 为每个段落添加其所属的标题类别
        processed_data.at[i, 'title_category'] = current_title_category

    # 添加标题类别作为特征
    processed_data['combined_feature'] = processed_data.apply(
        lambda x: f"{x['paragraph']} [TITLE_CATEGORY: {x['title_category']}]" if x['title_category'] else x['paragraph'],
        axis=1
    )

    return processed_data


def apply_smote(X_train_tfidf: Any, y_train: Any) -> tuple[Any, Any]:
    """
    应用SMOTE进行过采样

    Args:
        X_train_tfidf: 训练特征
        y_train: 训练标签

    Returns:
        tuple: 重采样后的特征和标签
    """
    try:
        print("正在进行数据增强...")
        train_logger.info("正在进行数据增强...")
        smote = SMOTE(random_state=42, k_neighbors=2)
        result = smote.fit_resample(X_train_tfidf, y_train)
        X_train_resampled = result[0]
        y_train_resampled = result[1]
        print("SMOTE数据增强成功")
        train_logger.info("SMOTE数据增强成功")
        return X_train_resampled, y_train_resampled
    except Exception as e:
        print(f"SMOTE数据增强失败: {e}，使用原始数据继续")
        train_logger.warning(f"SMOTE数据增强失败: {e}，使用原始数据继续")
        return X_train_tfidf, y_train


def create_models() -> dict[str, Any]:
    """
    创建分类模型字典

    Returns:
        dict: 模型名称到模型实例的映射
    """
    return {
        "逻辑回归": LogisticRegression(max_iter=1000, class_weight='balanced'),
        "随机森林": RandomForestClassifier(n_estimators=100, class_weight='balanced'),
        "梯度提升": GradientBoostingClassifier(n_estimators=100),
        "支持向量机": SVC(kernel='linear', probability=True, class_weight='balanced'),
        "朴素贝叶斯": MultinomialNB(),
        "决策树": DecisionTreeClassifier(class_weight='balanced')
    }


def train_and_evaluate_models(
    models: dict[str, Any],
    X_train: Any,
    y_train: Any,
    X_test: Any,
    y_test: Any,
    label_encoder: LabelEncoder
) -> tuple[dict[str, float], dict[str, Any]]:
    """
    训练并评估多个模型

    Args:
        models: 模型字典
        X_train: 训练特征
        y_train: 训练标签
        X_test: 测试特征
        y_test: 测试标签
        label_encoder: 标签编码器

    Returns:
        tuple: 模型得分和训练好的模型
    """
    model_scores: dict[str, float] = {}
    trained_models: dict[str, Any] = {}

    for name, model in models.items():
        print(f"训练 {name} 模型...")
        train_logger.info(f"训练 {name} 模型...")
        model.fit(X_train, y_train)
        trained_models[name] = model

        # 在测试集上评估
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        model_scores[name] = accuracy

        print(f"{name} 准确率: {accuracy:.4f}")
        train_logger.info(f"{name} 准确率: {accuracy:.4f}")

        # 详细分类报告
        actual_classes = np.unique(y_test)
        target_names = label_encoder.inverse_transform(actual_classes)
        report = classification_report(y_test, y_pred, labels=actual_classes, target_names=target_names)
        print(f"{name} 分类报告:")
        train_logger.info(f"{name} 分类报告:")
        print(report)
        train_logger.info(report)

    return model_scores, trained_models


def create_ensemble(
    model_scores: dict[str, float],
    trained_models: dict[str, Any],
    X_train: Any,
    y_train: Any,
    X_test: Any,
    y_test: Any,
    label_encoder: LabelEncoder
) -> Any:
    """
    创建并评估集成模型

    Args:
        model_scores: 模型得分
        trained_models: 训练好的模型
        X_train: 训练特征
        y_train: 训练标签
        X_test: 测试特征
        y_test: 测试标签
        label_encoder: 标签编码器

    Returns:
        Any: 集成模型
    """
    # 选择前3个最佳模型
    best_models = sorted(model_scores.items(), key=lambda x: x[1], reverse=True)[:3]
    print("\n最佳模型:")
    train_logger.info("\n最佳模型:")
    for name, score in best_models:
        print(f"{name}: {score:.4f}")

    # 创建集成模型
    print("\n创建集成模型...")
    train_logger.info("\n创建集成模型...")
    estimators = [(name, trained_models[name]) for name, _ in best_models]
    ensemble = VotingClassifier(estimators=estimators, voting='soft')
    ensemble.fit(X_train, y_train)

    # 评估集成模型
    ensemble_pred = ensemble.predict(X_test)
    ensemble_accuracy = accuracy_score(y_test, ensemble_pred)
    print(f"集成模型准确率: {ensemble_accuracy:.4f}")
    train_logger.info(f"集成模型准确率: {ensemble_accuracy:.4f}")

    # 详细分类报告
    actual_classes = np.unique(y_test)
    target_names = label_encoder.inverse_transform(actual_classes)
    ensemble_report = classification_report(y_test, ensemble_pred, labels=actual_classes, target_names=target_names)
    print("集成模型分类报告:")
    print(ensemble_report)
    train_logger.info(ensemble_report)

    return ensemble


def save_models(
    best_models: list[tuple[str, float]],
    trained_models: dict[str, Any],
    ensemble: Any,
    vectorizer: TfidfVectorizer,
    label_encoder: LabelEncoder
) -> None:
    """
    保存模型和相关对象

    Args:
        best_models: 最佳模型列表
        trained_models: 训练好的模型
        ensemble: 集成模型
        vectorizer: 特征提取器
        label_encoder: 标签编码器
    """
    models_dir = Path('src/nlp/models')
    models_dir.mkdir(exist_ok=True, parents=True)

    # 保存最佳单个模型
    best_model_name = best_models[0][0]
    joblib.dump(trained_models[best_model_name], models_dir.joinpath('best_single_model.model'))
    print(f"最佳单个模型 ({best_model_name}) 已保存至 'models/best_single_model.model'")
    train_logger.info(f"最佳单个模型 ({best_model_name}) 已保存至'models/best_single_model.model'")

    # 保存集成模型
    joblib.dump(ensemble, models_dir.joinpath('ensemble_classifier.model'))
    print("集成模型已保存至 'models/ensemble_classifier.model'")
    train_logger.info("集成模型已保存至'models/ensemble_classifier.model'")

    # 保存向量器和标签编码器
    joblib.dump(vectorizer, models_dir.joinpath('tfidf_vectorizer.model'))
    print("向量器已保存至 'models/tfidf_vectorizer.model'")
    train_logger.info("向量器已保存至'models/tfidf_vectorizer.model'")

    joblib.dump(label_encoder, models_dir.joinpath('label_encoder.model'))
    print("标签编码器已保存至 'models/label_encoder.model'")
    train_logger.info("标签编码器已保存至'models/label_encoder.model'")

    # 保存所有训练好的模型
    for name, model in trained_models.items():
        safe_name = name.replace(" ", "_")
        joblib.dump(model, models_dir.joinpath(f'{safe_name}.model'))
        print(f"{name} 模型已保存至 'models/{safe_name}.model'")
        train_logger.info(f"{name} 模型已保存至'models/{safe_name}.model'")


def train(data: DataFrame) -> None:
    """
    训练模型的主函数

    Args:
        data: 训练数据
    """
    # 确保数据有 'paragraph' 和 'label' 两列
    if 'paragraph' not in data.columns or 'label' not in data.columns:
        raise ValueError("数据集应包含 'paragraph' 和 'label' 两列。")

    # 1. 添加上下文特征
    print("正在添加上下文特征...")
    train_logger.info("正在添加上下文特征...")
    data = preprocess_data_with_context(data)

    # 显示数据分布
    label_counts: Counter[str] = Counter(data['label'])
    print("数据分布:")
    train_logger.info("数据分布:")
    for label, count in label_counts.items():
        print(f"{label}: {count}")

    # 2. 文本预处理
    print("正在预处理文本...")
    train_logger.info("正在预处理文本...")
    data['processed_paragraph'] = data['combined_feature'].apply(preprocess_text)

    # 3. 标签编码
    label_encoder = LabelEncoder()
    data['label_encoded'] = label_encoder.fit_transform(data['label'])

    # 4. 分割训练集和测试集
    X = data['processed_paragraph']
    y = data['label_encoded']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    # 5. 特征提取
    print("正在提取特征...")
    train_logger.info("正在提取特征...")
    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),  # 使用1-gram和2-gram
        min_df=2,            # 至少出现2次的词才考虑
        use_idf=True,
        sublinear_tf=True    # 使用次线性TF缩放
    )

    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)

    # 6. 应用SMOTE进行过采样
    X_train_resampled, y_train_resampled = apply_smote(X_train_tfidf, y_train)

    # 7. 创建模型
    print("正在训练多个模型...")
    train_logger.info("正在训练多个模型...")
    models = create_models()

    # 8. 训练并评估模型
    model_scores, trained_models = train_and_evaluate_models(
        models, X_train_resampled, y_train_resampled, X_test_tfidf, y_test, label_encoder
    )

    # 9. 创建集成模型
    best_models = sorted(model_scores.items(), key=lambda x: x[1], reverse=True)[:3]
    ensemble = create_ensemble(
        model_scores, trained_models, X_train_tfidf, y_train, X_test_tfidf, y_test, label_encoder
    )

    # 10. 保存模型
    save_models(best_models, trained_models, ensemble, vectorizer, label_encoder)


def train_model() -> None:
    """
    训练模型的入口函数
    """
    try:
        # 1. 加载数据集
        print("正在加载数据...")
        train_logger.info("正在加载数据...")
        data: DataFrame = get_merge_csv_data()

        # 2. 训练模型
        train(data)

        # 3. 更新CSV文件
        replace_old_csv()

        print("模型训练完成！")
        train_logger.info("模型训练完成！")
    except Exception as e:
        print(f"训练过程中发生错误: {e}")
        train_logger.error("训练过程中发生错误: %s", e, exc_info=True)
