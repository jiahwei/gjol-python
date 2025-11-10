# gjol-python

## git 子模块

拉取后需要初始化子模块

```bash
git submodule update --init --recursive
```

## 环境准备

安装 `pyenv` 和 `pyenv-virtualenv`

### win

prowershell安装[pyenv](https://pyenv-win.github.io/pyenv-win/#introduction)和[pyenv-win-venv](https://github.com/pyenv-win/pyenv-win-venv)

```prowershell
pyenv virtualenv 3.11.8 gjol-server-311
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"
# 重启prowershell
# 重新打开 PowerShell
# 运行 以检查安装是否成功。pyenv --version
# 安装pyenv-venv
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win-venv/main/bin/install-pyenv-win-venv.ps1" -OutFile "$HOME\install-pyenv-win-venv.ps1";
&"$HOME\install-pyenv-win-venv.ps1"
# 设置环境变量
[System.Environment]::SetEnvironmentVariable('path', $env:USERPROFILE + "\.pyenv-win-venv\bin;"  + [System.Environment]::GetEnvironmentVariable('path', "User"),"User")
```

#### 设置VSCode

1打开 VSCode 设置：
点击左下角的齿轮图标，然后选择“设置”。或者使用快捷键 Ctrl + , 打开设置。
2.搜索 Python 设置：
在设置搜索栏中输入 python.venvPath。
3.添加虚拟环境路径：
在 Python: Venv Path 设置中，输入你的虚拟环境路径：C:\Users\Jhw\.pyenv-win-venv\envs

### MAC

新建一个虚拟环境 `gjol-server-311`或者其他什么名字

使用 homebrew安装

## 创建环境

```bash
# mac/linux
pyenv virtualenv 3.11.8 gjol-server-311
pyenv activate gjol-server-311
# windows
pyenv-venv install 3.11.8 gjol-server-311
pyenv-venv activate gjol-server-311
```

## 下载依赖

```bash
pip install -r requirements.txt
pip freeze > requirements.tx
# 阿里云镜像
pip install -r requirements.txt -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
```

## 本地启动 FAST API 测试

```bash
uvicorn src.main:app --reload
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

同时支持IPv4和ipv6

```bash
uvicorn src.main:app --host :: --port 8000
```

## 服务器启动脚本（非Docker）

```bash
gunicorn src.main:app -c gunicorn.py
```
