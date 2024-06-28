import os  
import time  
import ssl  
import json
import uuid
import random
import numpy as np
from dotenv import load_dotenv  
from paho.mqtt import client as mqtt  
from urllib.parse import quote_plus, urlencode  
from hmac import HMAC  
from hashlib import sha256  
from datetime import datetime
from base64 import b64encode, b64decode  
from opcua import ua, Server

# 準備事項
# MessageType, PublisherId を設定して下さい
  
def generate_sas_token(uri, key, expiry=3600):  
    ttl = time.time() + expiry  
    sign_key = "%s\n%d" % ((quote_plus(uri)), int(ttl))  
    signature = b64encode(HMAC(b64decode(key), sign_key.encode("utf-8"), sha256).digest())  
    rawtoken = {  
        'sr': uri,  
        'sig': signature,  
        'se': str(int(ttl))  
    }  
    rvalue = 'SharedAccessSignature ' + urlencode(rawtoken)  
    return rvalue  
  
def create_mqtt_client():  
    username = f"{iot_hub_hostname}/{device_id}/?api-version=2020-09-30"  
    client = mqtt.Client(client_id=device_id, protocol=mqtt.MQTTv311)  
    client.username_pw_set(username=username, password=sas_token)  
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
  
def send_opcua_message(client, message):  
    # OPC UAのデータをエンコードしてJSON形式で送信  
    payload = json.dumps(message)  
    client.publish(f"devices/{device_id}/messages/events/", payload)  

# 指定範囲内の数値を生成する関数
def generate_clipped_normal(mean, std_dev, lower_bound, upper_bound):
    while True:
        sample = np.random.normal(mean, std_dev)
        if lower_bound <= sample <= upper_bound:
            return sample

def generate_sin_data(t, amp, freq, phase):
    # 正弦波の生成
    y = amp * np.sin(2 * np.pi * freq * t + phase)
    return y

def gen_noise(status):
    if status == 1:
        return 0
    elif status == 2:
        return 0.01 * random.randint(0, 100) - 0.5
    elif status == 3:
        return 0.02 * random.randint(0, 100) - 1.0
    else:
        return 0

# .envファイルを読み込む  
load_dotenv()  
  
# Azure IoT Hubの接続情報  
iot_hub_hostname = os.getenv("IOT_HUB_HOSTNAME")  
device_id = os.getenv("DEVICE_ID")  
key = os.getenv("KEY")  
uri = iot_hub_hostname + "/devices/" + device_id  
sas_token = generate_sas_token(uri, key, expiry=7776000) 

# MQTT クライアントのインスタンス  
mqtt_client = create_mqtt_client()  
  
# コールバック関数の設定  
mqtt_client.on_connect = on_connect  
mqtt_client.on_publish = on_publish  
  
# 接続  
mqtt_client.connect(iot_hub_hostname, port=8883)  
  
# 通信を非同期で開始  
mqtt_client.loop_start()  

total = 0

while True:
    state = (total // 40) % 3 + 1
    
    t = time.time()
    generated_value_1 = generate_sin_data(t, 3, 1/7, 0) + 3 * gen_noise(state)
    generated_value_2 = generate_sin_data(t, 5, 1/5, 0) + 5 * gen_noise(state)
    generated_value_3 = generate_sin_data(t, 7, 1/3, 0) + 7 * gen_noise(state)
    
    timestamp = datetime.utcnow().isoformat() + "Z" 

    message = {
        "MessageId": str(uuid.uuid4()),
        "MessageType": "",
        "PublisherId": "",
        "Messages": [
            {
                "Timestamp": timestamp,
                "Payload": {
                    "1": {
                        "Value": generated_value_1,
                        "SourceTimestamp": timestamp,
                        "ServerTimestamp": timestamp
                    },
                    "2": {
                        "Value": generated_value_2,
                        "SourceTimestamp": timestamp,
                        "ServerTimestamp": timestamp
                    },
                    "3": {
                        "Value": generated_value_3,
                        "SourceTimestamp": timestamp,
                        "ServerTimestamp": timestamp
                    }
                }
            }
        ]
    }
    
    # メッセージの送信  
    send_opcua_message(mqtt_client, message)  
    
    total += 1

    # 送信待機  
    time.sleep(1)  
  
# 通信終了  
mqtt_client.loop_stop()  
mqtt_client.disconnect()  
