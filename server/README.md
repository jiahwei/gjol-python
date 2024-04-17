# 脚本启动

在`main.py`中，创建 FASTAPI 实例

```Python
app = FastAPI()
```

## 本地测试 FAST API 启动命令

```console
uvicorn main:app --reload
```

## 服务器启动脚本

```bash
gunicorn main:app -c gunicorn.py
```