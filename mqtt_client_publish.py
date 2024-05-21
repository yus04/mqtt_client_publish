import os
import time
import ssl
import json
from dotenv import load_dotenv
from paho.mqtt import client as mqtt
from urllib.parse import quote_plus, urlencode
from hmac import HMAC
from hashlib import sha256
from base64 import b64encode, b64decode

def generate_sas_token(uri, key, expiry=3600):
    ttl = time.time() + expiry
    sign_key = "%s\n%d" % ((quote_plus(uri)), int(ttl))
    signature = b64encode(HMAC(b64decode(key), sign_key.encode("utf-8"), sha256).digest())

    rawtoken = {
        'sr' :  uri,
        'sig': signature,
        'se' : str(int(ttl))
        }

    rvalue = 'SharedAccessSignature ' + urlencode(rawtoken)

    return rvalue

def create_mqtt_client():
    username = f"{iot_hub_hostname}/{device_id}/?api-version=2020-09-30"
    client = mqtt.Client(client_id = device_id, protocol = mqtt.MQTTv311)

	# SASトークンを使用して認証
    client.username_pw_set(username=username, password = sas_token)
    
    # TLS設定
    client.tls_set_context(ssl.create_default_context())
    client.tls_insecure_set(True)
    
    return client

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to IoT Hub")
    else:
        print(f"Failed to connect with result code {rc}")

def on_publish(client, userdata, mid):
    print(f"Message {mid} published")
    
def send_message(client, message):
    payload = json.dumps(message)
    client.publish(f"devices/{device_id}/messages/events/", payload)

# .envファイルを読み込む
load_dotenv()

# Azure IoT Hubの接続情報
iot_hub_hostname = os.getenv("IOT_HUB_HOSTNAME")
device_id = os.getenv("DEVICE_ID")
key = os.getenv("KEY")
uri = iot_hub_hostname + "/devices/" + device_id
sas_token = generate_sas_token(uri, key, expiry=3600)

# MQTT クライアントのインスタンス
mqtt_client = create_mqtt_client()
    
# コールバック関数の設定
mqtt_client.on_connect = on_connect
mqtt_client.on_publish = on_publish

# 接続
mqtt_client.connect(iot_hub_hostname, port=8883)

# 通信を非同期で開始
mqtt_client.loop_start()

# 送信するメッセージ
message = {}

# メッセージの送信
send_message(mqtt_client, message)

# 送信待機
time.sleep(2)

# 通信終了
mqtt_client.loop_stop()
mqtt_client.disconnect()
