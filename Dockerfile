FROM python:3.9-slim

WORKDIR /app

# Cài đặt các thư viện hệ thống cần thiết cho thư viện âm thanh hoặc ONNX
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt các thư viện Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn vào image
COPY . .

# Expose cổng 7860 cho Hugging Face
EXPOSE 7860

# Mở user quyền truy cập cho Hugging Face Spaces (yêu cầu user không phải root)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app
COPY --chown=user . $HOME/app

# Khởi chạy server
CMD ["python", "app.py"]
