FROM python:3.11-slim

WORKDIR /app

# lxml用（安全策）
RUN apt-get update && apt-get install -y \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 依存だけ先に入れる（キャッシュ効率）
COPY scraper/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 開発用なので bash 起動
CMD ["bash"]