from sqlalchemy import create_engine, Select, asc, desc, Table, MetaData
from models import teams,challenges,challenges_data,Session,Base,raw_data
import paho.mqtt.client as mqtt
import json
from dateutil import parser


# MQTT configuration
MQTT_USER = "mqttclient"        # Replace "mqttclient" with the actual MQTT username 
MQTT_PASSWORD = "Kennwort1"     # Replace "Kennwort1" with the actual MQTT password 

# Database configuration
DB_USER = "mariadbclient"       # Replace "mariadbclient" with the actual database user 
DB_PASSWORD = "Kennwort1"       # Replace "Kennwort1" with the actual database password 




# constants for MQTT and Database configurations
SERVER_IPADRESS = "127.0.0.1"
MQTT_PORT = 1883
DB_PORT = '3306'  
DB_NAME = 'Zeitmessung'


db_url = f'mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{SERVER_IPADRESS}:{DB_PORT}/{DB_NAME}'
engine_db = create_engine(db_url)
Session_db = Session(bind = engine_db)

Base.metadata.create_all(bind=engine_db)


def on_connect(client, userdata, flags, rc):
    client.subscribe("esp32/timestamp",qos=2)


def on_message(client, userdata, message):
    payload = message.payload.decode("utf-8")

    if message.topic == "esp32/timestamp" :
        data_json = json.loads(payload)
        data = raw_data()

        if data_json['esp_id']:
            data.esp_id = data_json['esp_id']

        if data_json['timestamp']:
            data.timestamp = parser.isoparse(data_json['timestamp'])

        Session_db.add(data)
        Session_db.commit()

def start_mqtt_client():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.connect(SERVER_IPADRESS, MQTT_PORT, 60)
    client.loop_forever()

start_mqtt_client()
