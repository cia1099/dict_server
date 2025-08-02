# 使用Python 3.13官方镜像作为基础镜像，支持多架构（amd64/arm64）
FROM python:3.13-slim

# 更新包管理器并安装git
RUN apt-get update && \
    apt-get install -y git ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# 克隆指定的仓库并切换到dev分支，直接克隆到/dict_server
RUN git clone https://github.com/cia1099/dict_server.git /dict_server && \
    cd /dict_server && \
    git checkout dev

# 设置工作目录
WORKDIR /dict_server

# 复制本地配置文件到容器中的dict_server目录
COPY .env ./
COPY requirements.txt ./
COPY ai-vocabulary-firebase-firebase-adminsdk-fbsvc-d4300d6e1d.json ./
COPY china-wall-over-1eb9183af042.json ./

# 复制数据库文件到指定路径
COPY dictionary/oxfordstu.db dictionary/

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露8866端口
EXPOSE 8866

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8866"]
