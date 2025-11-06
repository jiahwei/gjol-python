FROM python:3.11.8 AS gjol

WORKDIR /code

#设置时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
# 创建预留的文件夹
RUN mkdir -p /code/bulletins /code/bulletins/routine /code/bulletins/skill /code/bulletins/version

COPY ./requirements.txt /code/requirements.txt

ENV PIP_DEFAULT_TIMEOUT=60
RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel -i http://mirrors.aliyun.com/pypi/simple --trusted-host mirrors.aliyun.com
RUN pip install --no-cache-dir -i http://mirrors.aliyun.com/pypi/simple --trusted-host mirrors.aliyun.com -r /code/requirements.txt

COPY ./constants.py /code/constants.py

# 数据库
COPY ./sqlite /code/sqlite
# code
COPY ./src /code/src

# 确保日志目录存在
RUN mkdir -p /code/src/logs

# 设置权限
RUN chmod -R 755 /code

# 设置生产环境变量
ENV ENV=production

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--root-path", "/api"]