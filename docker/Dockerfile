FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY pyproject.toml requirements.runtime.lock README.md ./
COPY src ./src
RUN pip install --no-cache-dir -r requirements.runtime.lock \
    && pip install --no-cache-dir --no-deps . \
    && pip check
COPY . .
