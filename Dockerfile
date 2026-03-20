FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

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
RUN cd /app/reportlab && PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true npm install

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

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
