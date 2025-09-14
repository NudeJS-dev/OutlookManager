FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 创建非root用户
RUN useradd -m -u 1000 outlook && chown -R outlook:outlook /app
USER outlook

EXPOSE 8000

CMD ["python", "main.py"]