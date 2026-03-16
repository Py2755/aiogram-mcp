FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY pyproject.toml README.md LICENSE ./
COPY aiogram_mcp/ aiogram_mcp/
COPY examples/ examples/

RUN pip install --no-cache-dir .

CMD ["python", "-m", "aiogram_mcp"]
