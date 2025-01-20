import paho.mqtt.client as mqtt
import sqlite3
from datetime import datetime
import pytz

# MQTT Broker details
BROKER = "broker.hivemq.com"
PORT = 1883
TOPICS = ["FEEDME", "alerts"]  # Include both FEEDME and alerts topics

# SQLite database file
DB_FILE = "iot_data.db"

# Timezone for Israel
ISRAEL_TZ = pytz.timezone("Asia/Jerusalem")

# Create the SQLite database and table if they don't exist
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
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    local_time = datetime.now(ISRAEL_TZ).strftime('%Y-%m-%d %H:%M:%S')  # Local time in Israel
    cursor.execute('''
    INSERT INTO sensor_data (timestamp, topic, message) VALUES (?, ?, ?)
    ''', (local_time, topic, message))
    conn.commit()
    conn.close()
    print(f"Data saved: Timestamp={local_time}, Topic={topic}, Message={message}")

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

    # Check for critical conditions and send alerts if topic is 'FEEDME'
    if topic == "FEEDME" and "Weight:" in message:
        try:
            weight = int(message.split(":")[1].split()[0])  # Extract weight
            if weight < 3:  # Critical condition (weight < 3 grams)
                alert_message = f"Critical weight detected: {weight} grams"
                print(alert_message)
                client.publish("alerts", alert_message)  # Publish to alerts topic
                insert_data("alerts", alert_message)  # Save alert to DB
        except ValueError:
            print("Error parsing weight from message")

# Create and configure MQTT client
client = mqtt.Client("DataManager")
client.on_connect = on_connect
client.on_message = on_message

# Connect to the broker
client.connect(BROKER, PORT)
client.loop_start()

# Ensure the database is created
create_database()

# Keep the script running
try:
    while True:
        pass
except KeyboardInterrupt:
    client.loop_stop()
    client.disconnect()
