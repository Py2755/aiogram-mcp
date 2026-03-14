FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY aiogram_mcp/ aiogram_mcp/
COPY examples/ examples/

RUN pip install --no-cache-dir .

CMD ["python", "examples/basic_bot.py"]
