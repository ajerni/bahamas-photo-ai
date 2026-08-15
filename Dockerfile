# syntax=docker/dockerfile:1

FROM node:22-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend ./
ENV VITE_API_BASE_URL=""
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PMM_DATABASE_URL=sqlite:////data/private_memory_map.db \
    PMM_FRONTEND_DIR=/app/frontend/dist \
    PMM_ENABLE_BASIC_AUTH=true
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend
COPY --from=frontend /app/frontend/dist ./frontend/dist
VOLUME /data
EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
