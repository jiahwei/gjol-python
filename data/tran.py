import csv
import json
from pathlib import Path


def csv_to_json(csv_name):
    input_file = Path(f"data/uncheck/{csv_name}.csv")
    output_file = Path(f"data/uncheck/{csv_name}.json")
    data = []

    with open(input_file, mode='r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            # 重命名键
            row['text'] = row.pop('paragraph')
            data.append({"data": row})

    with open(output_file, mode='w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

    print("转换完成，数据已保存到", output_file)


csv_to_json("paragraph_2025-03-08_16-43-30")