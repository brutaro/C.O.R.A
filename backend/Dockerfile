# Stage 1: Build Frontend
FROM node:18-alpine as frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./

# Pass environment variables to the build
ARG REACT_APP_FIREBASE_API_KEY
ARG REACT_APP_FIREBASE_AUTH_DOMAIN
ARG REACT_APP_FIREBASE_PROJECT_ID
ARG REACT_APP_FIREBASE_STORAGE_BUCKET
ARG REACT_APP_FIREBASE_MESSAGING_SENDER_ID
ARG REACT_APP_FIREBASE_APP_ID
ARG REACT_APP_FIREBASE_APP_NAME
ARG REACT_APP_API_URL

ENV REACT_APP_FIREBASE_API_KEY=$REACT_APP_FIREBASE_API_KEY
ENV REACT_APP_FIREBASE_AUTH_DOMAIN=$REACT_APP_FIREBASE_AUTH_DOMAIN
ENV REACT_APP_FIREBASE_PROJECT_ID=$REACT_APP_FIREBASE_PROJECT_ID
ENV REACT_APP_FIREBASE_STORAGE_BUCKET=$REACT_APP_FIREBASE_STORAGE_BUCKET
ENV REACT_APP_FIREBASE_MESSAGING_SENDER_ID=$REACT_APP_FIREBASE_MESSAGING_SENDER_ID
ENV REACT_APP_FIREBASE_APP_ID=$REACT_APP_FIREBASE_APP_ID
ENV REACT_APP_FIREBASE_APP_NAME=$REACT_APP_FIREBASE_APP_NAME
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# Force CI=false to ignore warnings as errors
RUN CI=false npm run build

# Stage 2: Setup Backend & Runtime
FROM python:3.10-slim
WORKDIR /app

# Install system dependencies (Chromium for Puppeteer + Node.js)
# Node.js is needed for Puppeteer script execution
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    nodejs \
    npm \
    fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install reportlab Node dependencies used for PDF generation
COPY reportlab/package*.json ./reportlab/
RUN cd /app/reportlab && PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true npm install

# Copy Backend Code
COPY src ./src
COPY main.py .
COPY auth.py .
COPY reportlab ./reportlab
COPY prompts ./prompts

# Copy Frontend Build from Stage 1
# We copy to frontend/build because main.py expects it there (or we can adjust main.py)
# Based on previous steps, main.py looks in frontend_build first, then frontend/build.
# Let's stick to the standard frontend/build structure for Docker.
COPY --from=frontend-build /app/frontend/build /app/frontend/build
# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

# Expose port
EXPOSE $PORT

# Start command
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
