FROM python:3.13-slim AS builder

WORKDIR /app

# 必要なパッケージをインストール
RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

# リポジトリをクローン
RUN git clone --depth 1 https://github.com/shohei81/HN_summarizer.git .

# 依存関係をインストール
ENV PYTHONPATH=/app/site-packages
RUN pip --no-cache-dir install --upgrade pip && \
    pip install --no-cache-dir --target site-packages -r requirements.txt

# ログディレクトリを作成
RUN mkdir -p /app/logs && chmod -R 777 /app/logs

# 実行ステージ
FROM gcr.io/distroless/python3-debian12:nonroot

WORKDIR /app

# ビルドステージからファイルをコピー
COPY --from=builder /app .

# 環境変数を設定
ENV PYTHONPATH=/app/site-packages \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Secret Managerの認証に関する注意事項
# 注意: Secret Managerを使用するには、以下のいずれかの方法で認証情報を提供する必要があります:
# 1. コンテナ実行時に環境変数 GOOGLE_APPLICATION_CREDENTIALS を設定し、サービスアカウントキーをマウント
#    例: docker run -v /path/to/key.json:/tmp/key.json -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/key.json ...
# 2. GKEやCloud Run上で実行する場合は、適切なIAMロールを持つサービスアカウントを使用

# エントリーポイントを設定
CMD ["python", "./src/main.py", "--config", "config.yaml"]
