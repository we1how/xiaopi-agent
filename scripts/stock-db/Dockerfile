FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制脚本
COPY *.py .

# 创建数据目录
RUN mkdir -p /data/parquet /data/meta /data/logs

# 设置环境变量
ENV STOCK_DATA_PATH=/data
ENV PYTHONUNBUFFERED=1

# 默认执行每日更新
CMD ["python", "daily_update.py", "--base-path", "/data"]
