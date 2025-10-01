FROM python:3.11-slim

WORKDIR /app

# 🔹 Instalar dependencias del sistema para OpenCV y Pyzbar
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libzbar0 \
    v4l-utils \
    && rm -rf /var/lib/apt/lists/*

# 🔹 Copiar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# (opcional) Si no quieres requirements.txt puedes instalar directo:
# RUN pip install --no-cache-dir requests opencv-python pyzbar qrcode pillow

# 🔹 Copiar el código
COPY app/ .

CMD ["python", "main.py"]
