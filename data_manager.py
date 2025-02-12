import paho.mqtt.client as mqtt
import sqlite3
from datetime import datetime
import pytz

BROKER = "broker.hivemq.com"
PORT = 1883
TOPICS = ["FEEDME", "alerts"]  

DB_FILE = "iot_data.db"

ISRAEL_TZ = pytz.timezone("Asia/Jerusalem")

def create_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sensor_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME NOT NULL,
        topic TEXT NOT NULL,
        message TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()
    print("Database and table created successfully!")

# Insert data into the SQLite database with local timestamp
def insert_data(topic, message):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        local_time = datetime.now(ISRAEL_TZ).strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute('''
            INSERT INTO sensor_data (timestamp, topic, message) VALUES (?, ?, ?)
        ''', (local_time, topic, message))

        conn.commit()
        print(f"Data saved: Timestamp={local_time}, Topic={topic}, Message={message}")

    except sqlite3.Error as e:
        print(f"Database Insert Error: {e}")

    finally:
        if conn:
            conn.close()

# Callback when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        for topic in TOPICS:
            client.subscribe(topic)
            print(f"Subscribed to topic: {topic}")
    else:
        print(f"Failed to connect, return code {rc}")

# Callback when a message is received
def on_message(client, userdata, msg):
    topic = msg.topic
    message = msg.payload.decode()
    print(f"Message received on topic {topic}: {message}")

    # Save data to SQLite
    insert_data(topic, message)

    if topic == "FEEDME" and "Weight:" in message:
        try:
            weight = int(message.split(":")[1].split()[0])  
            if weight < 3:  
                alert_message = f"Critical weight detected: {weight} grams"
                print(alert_message)
                client.publish("alerts", alert_message)  
                insert_data("alerts", alert_message)  
        except ValueError:
            print("Error parsing weight from message")

client = mqtt.Client("DataManager")
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT)
client.loop_start()

create_database()

try:
    while True:
        pass
except KeyboardInterrupt:
    client.loop_stop()
    client.disconnect()
