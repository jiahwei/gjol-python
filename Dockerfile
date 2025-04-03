FROM python:3.11.8 AS gjol

WORKDIR /code

# 创建预留的文件夹
RUN mkdir -p /code/bulletins /code/bulletins/routine /code/bulletins/skill /code/bulletins/version

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./util /code/util
COPY ./constants.py /code/constants.py

# 数据库
COPY ./sqlite /code/sqlite
# code
COPY ./src /code/src

# 确保日志目录存在
RUN mkdir -p /code/src/logs

# 设置权限
RUN chmod -R 755 /code

CMD ["uvicorn", "src.main:app","--host", "0.0.0.0", "--port", "8000"]