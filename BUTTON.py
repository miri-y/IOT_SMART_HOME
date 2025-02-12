import os
import sys
import random
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import *
import paho.mqtt.client as mqtt
from mqtt_init import *

global clientname, CONNECTED
CONNECTED = False
r = random.randrange(1, 10000000)
clientname = "IOT_client-Id-" + str(r)
BUTTON_topic = "FEEDME"

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
        print(f"Connecting to broker {self.broker} on port {self.port}")
        self.client.connect(self.broker, self.port)
        self.client.loop_start()

    def publish_to(self, topic, message):
        if CONNECTED:
            self.client.publish(topic, message)
            print(f"Published to {topic}: {message}") 
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

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.mc = Mqtt_client()
        self.mc.connect_to()

        self.setGeometry(100, 100, 400, 300)
        self.setWindowTitle('Manual Feeding Button')

        # Add a manual feed button
        self.feed_button = QPushButton("Feed Now", self)
        self.feed_button.setGeometry(150, 80, 100, 40)
        self.feed_button.setStyleSheet("background-color: red; color: white; font-size: 16px;")
        self.feed_button.clicked.connect(self.feed_now)

        # Add a stop button
        self.stop_button = QPushButton("Stop", self)
        self.stop_button.setGeometry(150, 150, 100, 40)
        self.stop_button.setStyleSheet("background-color: orange; color: white; font-size: 16px;")
        self.stop_button.clicked.connect(self.stop_relay)

    def feed_now(self):
        """Handle manual feeding button press."""
        print("Manual feeding triggered")
        self.mc.publish_to(BUTTON_topic, "Manual feeding triggered")
        self.feed_button.setStyleSheet("background-color: green; color: white; font-size: 16px;")
        self.feed_button.setText("Feeding...")
        QtCore.QTimer.singleShot(3000, self.reset_feed_button)

    def stop_relay(self):
        """Handle stop button press."""
        print("Stop relay triggered")
        self.mc.publish_to(BUTTON_topic, "Stop relay")
        self.stop_button.setStyleSheet("background-color: red; color: white; font-size: 16px;")
        self.stop_button.setText("Stopping...")
        QtCore.QTimer.singleShot(3000, self.reset_stop_button)

    def reset_feed_button(self):
        """Reset the feed button to its default state."""
        self.feed_button.setStyleSheet("background-color: red; color: white; font-size: 16px;")
        self.feed_button.setText("Feed Now")

    def reset_stop_button(self):
        """Reset the stop button to its default state."""
        self.stop_button.setStyleSheet("background-color: orange; color: white; font-size: 16px;")
        self.stop_button.setText("Stop")

app = QApplication(sys.argv)
mainwin = MainWindow()
mainwin.show()
app.exec_()
