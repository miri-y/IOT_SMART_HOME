import os
import sys
import random
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import paho.mqtt.client as mqtt
from mqtt_init import *  # Import MQTT broker settings

# Creating Client name - should be unique
global clientname, CONNECTED
CONNECTED = False
r = random.randrange(1, 10000000)
clientname = "IOT_client-Id234-" + str(r)
DHT_topic = pub_topics[0]  
update_rate = 5000  # in milliseconds

class Mqtt_client():
    def __init__(self):
        self.broker = broker_ip
        self.port = int(broker_port)
        self.clientname = clientname
        self.username = username
        self.password = password

    def connect_to(self):
        self.client = mqtt.Client(self.clientname, clean_session=True)
        self.client.username_pw_set(self.username, self.password)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_log = self.on_log
        print(f"Connecting to broker {self.broker} on port {self.port}")
        self.client.connect(self.broker, self.port)

    def publish_to(self, topic, message):
        if CONNECTED:
            self.client.publish(topic, message)
        else:
            print("Can't publish. Connection not established.")

    def on_connect(self, client, userdata, flags, rc):
        global CONNECTED
        if rc == 0:
            print("Connected successfully")
            CONNECTED = True
        else:
            print("Connection failed. Code:", rc)

    def on_disconnect(self, client, userdata, flags, rc=0):
        global CONNECTED
        CONNECTED = False
        print("Disconnected. Code:", rc)

    def on_log(self, client, userdata, level, buf):
        print("log:", buf)

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.mc = Mqtt_client()
        self.mc.connect_to()
        self.mc.client.loop_start()

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(update_rate)

        self.setGeometry(100, 100, 400, 300)
        self.setWindowTitle('Weight Sensor')

        # Create UI components
        self.label_topic = QLabel(f"MQTT Topic: {DHT_topic}", self)
        self.label_topic.setGeometry(20, 20, 360, 30)
        self.label_topic.setStyleSheet("font-size: 14px; color: blue;")

        self.label_weight = QLabel("Current Weight: -- grams", self)
        self.label_weight.setGeometry(20, 80, 360, 40)
        self.label_weight.setStyleSheet("font-size: 16px; color: black; font-weight: bold;")

        self.label_status = QLabel("Status: Waiting for updates...", self)
        self.label_status.setGeometry(20, 140, 360, 30)
        self.label_status.setStyleSheet("font-size: 14px; color: gray;")

    def update_data(self):
        weight = random.randint(0, 50)  # Simulate weight measurement
        current_data = f'Weight: {weight} grams'
        print(f"Publishing weight: {current_data}")
        self.mc.publish_to(DHT_topic, current_data)

        # Update UI with the current weight
        self.label_weight.setText(f"Current Weight: {weight} grams")

        if weight < 10:
            warning_message = f"Low weight detected: {weight} grams"
            print(f"Publishing alert: {warning_message}")
            self.mc.publish_to(DHT_topic, warning_message)
            self.label_status.setText("Status: Low weight detected!")
            self.label_status.setStyleSheet("font-size: 14px; color: red;")
        else:
            self.label_status.setText("Status: Weight is sufficient.")
            self.label_status.setStyleSheet("font-size: 14px; color: green;")

app = QApplication(sys.argv)
mainwin = MainWindow()
mainwin.show()
app.exec_()
