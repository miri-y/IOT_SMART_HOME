import os
import sys
import random
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import *
import paho.mqtt.client as mqtt
from mqtt_init import *

# Global variables
global clientname, CONNECTED
CONNECTED = False
r = random.randrange(1, 10000000)
clientname = "IOT_client-Id-" + str(r)
RELAY_topics = ["FEEDME"]

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
        self.client.on_message = self.on_message
        print(f"Connecting to broker {self.broker} on port {self.port}")
        self.client.connect(self.broker, self.port)

    def start_listening(self):
        self.client.loop_start()
        for topic in RELAY_topics:
            self.client.subscribe(topic)
            print(f"Subscribed to topic: {topic}")

    def publish_to(self, topic, message):
        if CONNECTED:
            self.client.publish(topic, message)
            print(f"Published to topic '{topic}': {message}")
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

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        message = str(msg.payload.decode("utf-8", "ignore"))
        print(f"Message received on {topic}: {message}")

        if topic == pub_topics[0] and "Weight:" in message:
            try:
                weight = int(message.split(":")[1].split()[0])  
                print(f"Weight received: {weight} grams")

                if weight < 10:
                    if mainwin.status_label.text() != "Relay Status: ON":  
                        print("Activating relay due to low weight")
                        mainwin.update_ui_on(weight)
                else:
                    if mainwin.status_label.text() != "Relay Status: OFF":  
                        print("Deactivating relay - weight sufficient")
                        mainwin.update_ui_off()
            except ValueError:
                print("Error parsing weight from message")

        elif topic == pub_topics[1] and "Manual feeding triggered" in message:
            print("Activating relay due to manual feeding")
            mainwin.update_ui_on(None)
        elif topic == pub_topics[1] and "Stop relay" in message:
            print("Deactivating relay")
            mainwin.update_ui_off()

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.mc = Mqtt_client()
        self.mc.connect_to()
        self.mc.start_listening()

        self.setGeometry(100, 100, 400, 200)
        self.setWindowTitle('RELAY Controller')

        self.status_label = QLabel("Relay Status: OFF", self)
        self.status_label.setGeometry(100, 80, 200, 40)
        self.status_label.setStyleSheet("background-color: red; color: white; font-size: 16px; text-align: center;")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)

    def update_ui_on(self, weight):
        """Update the UI when the relay is activated and send a message to the broker."""
        self.status_label.setText("Relay Status: ON")
        self.status_label.setStyleSheet("background-color: green; color: white; font-size: 16px; text-align: center;")
        # Publish message to the FEEDME topic
        self.mc.publish_to("FEEDME", "Relay activated due to low weight")
        # Publish message to the alerts topic if weight is below 3 grams
        if weight is not None and weight < 3:
            self.mc.publish_to("alerts", f"Critical weight detected: {weight} grams")

    def update_ui_off(self):
        """Reset the UI to indicate the relay is off."""
        self.status_label.setText("Relay Status: OFF")
        self.status_label.setStyleSheet("background-color: red; color: white; font-size: 16px; text-align: center;")
        # Publish message to the FEEDME topic
        self.mc.publish_to("FEEDME", "Relay deactivated - weight sufficient")

app = QApplication(sys.argv)
mainwin = MainWindow()
mainwin.show()
app.exec_()
