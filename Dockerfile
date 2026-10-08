FROM node:22-alpine AS frontend
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir .
COPY --from=frontend /web/dist ./web/dist

ENV SMK_ROOT=/app \
    PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "smk_playground.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
