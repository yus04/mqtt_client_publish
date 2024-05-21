# mqtt_client_publish
MQTT クライアントを使い、メッセージを Publish するサンプルコードです。

## 前提
- Subscriber 側の設定は終えているものとします。

## 準備事項
- 必要なライブラリのインストール
- 環境変数の設定
- 送信データの設定

### 必要なライブラリのインストール
以下のコマンドを実行して必要なライブラリをインストールしてください。
```
pip install -r requirements.txt
```

### 環境変数の設定
.env.sample を参考にして、.env を設定してください。

### 送信データの設定
mqtt_client_publish.py の message に送信するデータを設定してください。
