# 使用Ubuntu 24.04 LTS作为基础镜像
FROM ubuntu:24.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV container=docker

# 更新包管理器并安装必要的系统依赖
RUN apt-get update && apt-get install -y \
    git \
    nginx \
    systemd \
    openssh-server \
    ffmpeg \
    vim curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 配置SSH服务
RUN mkdir -p /var/run/sshd \
    && echo 'root:password101' | chpasswd \
    && sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config \
    && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    && ssh-keygen -A

# 安装uv并安装Python 3.13
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    /root/.local/bin/uv python install 3.13
ENV PATH="/root/.local/bin:$PATH"

# 创建工作目录
WORKDIR /root

# 克隆仓库并切换到dev分支
RUN git clone https://github.com/cia1099/dict_server.git && \
    cd dict_server && \
    git checkout dev

# 设置工作目录为dict_server
WORKDIR /root/dict_server

# 复制Pipfile到容器中
COPY Pipfile .

# 创建Python 3.13虚拟环境并在其中安装pipenv和依赖
RUN $(/root/.local/bin/uv python find 3.13) -m venv venv && \
    . venv/bin/activate && \
    python -m pip install --upgrade pip && \
    python -m pip install pipenv && \
    python -m pipenv install --skip-lock

# 复制配置文件到容器中
COPY .env .
COPY ai-vocabulary-firebase-firebase-adminsdk-fbsvc-d4300d6e1d.json .
COPY china-wall-over-1eb9183af042.json .

# 确保cmd.sh具有执行权限
RUN chmod +x cmd.sh

# 创建dictionary目录并复制数据库文件
RUN mkdir -p dictionary
COPY dictionary/oxfordstu.db dictionary/

# 创建SSL证书目录
RUN mkdir -p /etc/ssl/cloudflare

# 复制SSL证书文件
COPY docker/origin.crt /etc/ssl/cloudflare/
COPY docker/origin.key /etc/ssl/cloudflare/

# 创建nginx配置文件
RUN mkdir -p /etc/nginx/sites-available && \
    echo 'server {\n\
    listen 443 ssl;\n\
    server_name cia1099.cloudns.ch;\n\
    # SSL configuration\n\
    ssl_certificate /etc/ssl/cloudflare/origin.crt;\n\
    ssl_certificate_key /etc/ssl/cloudflare/origin.key;\n\
\n\
    ssl_protocols TLSv1.2 TLSv1.3;\n\
    ssl_ciphers HIGH:!aNULL:!MD5;\n\
\n\
    location /dict/ {\n\
        proxy_pass http://localhost:8866/dict/;\n\
        proxy_set_header Host $host;\n\
        proxy_set_header X-Real-IP $remote_addr;\n\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n\
        proxy_set_header X-Forwarded-Proto $scheme;\n\
    }\n\
\n\
}\n\
\n\
server {\n\
    listen 80;\n\
    server_name www.cia1099.cloudns.ch;\n\
\n\
    return 301 https://$host$request_uri;\n\
}' > /etc/nginx/sites-available/cia1099.cloudns.ch

# 启用nginx站点
RUN ln -s /etc/nginx/sites-available/cia1099.cloudns.ch /etc/nginx/sites-enabled/

# 创建dict.service系统服务
RUN echo '[Unit]\n\
Description=Dict Server Application\n\
After=network.target\n\
\n\
[Service]\n\
Type=simple\n\
User=root\n\
WorkingDirectory=/root/dict_server\n\
Environment=PATH=/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\n\
ExecStart=/bin/bash /root/dict_server/cmd.sh\n\
Restart=on-failure\n\
RestartSec=5\n\
\n\
[Install]\n\
WantedBy=multi-user.target' > /usr/lib/systemd/system/dict.service

# 创建daily-reboot.service
RUN echo '[Unit]\n\
Description=Daily Reboot\n\
\n\
[Service]\n\
Type=oneshot\n\
ExecStart=/usr/sbin/reboot' > /etc/systemd/system/daily-reboot.service

# 创建daily-reboot.timer
RUN echo '[Unit]\n\
Description=Timer to reboot system daily\n\
\n\
[Timer]\n\
OnCalendar=*-*-* 05:15:00\n\
Persistent=true\n\
\n\
[Install]\n\
WantedBy=timers.target' > /etc/systemd/system/daily-reboot.timer

# 创建systemd目标目录并启用服务
RUN mkdir -p /etc/systemd/system/multi-user.target.wants && \
    mkdir -p /etc/systemd/system/timers.target.wants && \
    ln -sf /usr/lib/systemd/system/dict.service /etc/systemd/system/multi-user.target.wants/dict.service && \
    ln -sf /etc/systemd/system/daily-reboot.timer /etc/systemd/system/timers.target.wants/daily-reboot.timer && \
    ln -sf /lib/systemd/system/ssh.service /etc/systemd/system/multi-user.target.wants/ssh.service

# 创建启动脚本
RUN echo '#!/bin/bash\n\
# 启动SSH服务\n\
service ssh start\n\
\n\
# 激活Python虚拟环境并启动应用\n\
cd /root/dict_server\n\
source venv/bin/activate\n\
\n\
# 启动nginx\n\
nginx -g "daemon off;" \&\n\
\n\
# 启动应用\n\
if [ -f "cmd.sh" ]; then\n\
    chmod +x cmd.sh\n\
    ./cmd.sh \&\n\
fi\n\
\n\
# 保持容器运行\n\
wait' > /start.sh && \
    chmod +x /start.sh

# 暴露端口
EXPOSE 22 80 443 8866

# 设置启动命令
CMD ["/usr/bin/systemd"]
