FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./

RUN CI=false npm run build

FROM python:3.10-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    nodejs \
    npm \
    fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/reportlab/package*.json ./reportlab/
RUN cd /app/reportlab && PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true npm ci --omit=dev

COPY backend/src ./src
COPY backend/prompts ./prompts
COPY backend/main.py ./main.py
COPY backend/auth.py ./auth.py
COPY backend/firebase_config.py ./firebase_config.py
COPY backend/reportlab ./reportlab

COPY --from=frontend-build /app/frontend/build /app/frontend/build

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/api/health', timeout=4).status < 500 else 1)"

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
