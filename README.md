# gjol-python

## 环境准备

安装 `pyenv` 和 `pyenv-virtualenv`

新建一个虚拟环境 `gjol-server`或者其他什么名字

```bash
pyenv virtualenv 3.10.4 gjol-server
pyenv activate gjol-server
```

## 下载依赖

```bash
pip install -r requirements.txt
```

## 本地启动 FAST API 测试

```bash
uvicorn server.main:app --reload
```

## 服务器启动脚本

```bash
gunicorn main:app -c gunicorn.py
```
