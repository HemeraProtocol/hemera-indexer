# 使用 Python 基础镜像
FROM python:3.9-slim
COPY ./config /app/config

# 设置工作目录
WORKDIR /app

VOLUME /app/config


# 复制要求文件并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制 Python 脚本到容器
COPY alarm_data.py .

# 运行脚本
CMD ["python", "alarm_data.py"]
