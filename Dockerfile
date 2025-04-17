FROM python:3.13-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 https://github.com/shohei81/HN_summarizer.git .

ENV PYTHONPATH=/app/site-packages
RUN pip --no-cache-dir install --upgrade pip && \
    pip install --no-cache-dir --target site-packages -r requirements.txt

FROM gcr.io/distroless/python3-debian12:nonroot

WORKDIR /app

COPY --from=builder /app .

ENV PYTHONPATH=/app/site-packages
CMD ["python", "./src/main.py"]
