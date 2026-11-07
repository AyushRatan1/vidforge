FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg libgl1 libegl1 fontconfig fonts-noto-color-emoji curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
# Free voice model (~350 MB) and fonts baked into the image
RUN python run.py setup

ENV VIDFORGE_HOST=0.0.0.0 PORT=8000
EXPOSE 8000
VOLUME ["/app/data"]
HEALTHCHECK --interval=30s --timeout=5s CMD curl -fs http://127.0.0.1:8000/healthz || exit 1
CMD ["python", "run.py", "serve"]
