import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QLabel,
    QPushButton, QHeaderView
)
from PyQt5.QtCore import QTimer
import paho.mqtt.client as mqtt
from mqtt_init import *  

DB_FILE = "iot_data.db"

class MqttClient():
    def __init__(self, gui):
        self.client = mqtt.Client("GUI_Client")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.username_pw_set(username, password)
        self.client.connect(broker_ip, int(broker_port))
        self.client.loop_start()
        self.gui = gui  

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
            self.client.subscribe("FEEDME")
            self.client.subscribe("alerts")
        else:
            print(f"Failed to connect, return code {rc}")

    def on_message(self, client, userdata, msg):
        message = msg.payload.decode()
        print(f"Message received on topic {msg.topic}: {message}")

        if msg.topic == "FEEDME":
            if "Relay activated due to low weight" in message:
                self.gui.update_relay_status("ON")
            elif "Relay deactivated - weight sufficient" in message:
                 self.gui.update_relay_status("OFF")
        
        if msg.topic == "alerts" and "Critical weight detected" in message:
            self.gui.update_alert_status(message)

    def publish(self, topic, message):
        self.client.publish(topic, message)
        print(f"Published to {topic}: {message}")

class MainGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IoT System Dashboard")
        self.setGeometry(100, 100, 900, 600)
        self.mqtt_client = MqttClient(self)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()

        self.relay_status = QLabel("Relay Status: OFF", self)
        self.relay_status.setStyleSheet("font-size: 16px; color: red;")
        self.layout.addWidget(self.relay_status)

        self.alert_status = QLabel("No alerts", self)
        self.alert_status.setStyleSheet("font-size: 16px; color: blue;")
        self.layout.addWidget(self.alert_status)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Topic", "Message"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table)

        self.refresh_button = QPushButton("Refresh Data")
        self.refresh_button.clicked.connect(self.load_data)
        self.layout.addWidget(self.refresh_button)

        self.central_widget.setLayout(self.layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.load_data)
        self.timer.start(2000)  

        self.load_data()

    def load_data(self):
        """Load data from the database into the table."""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp, topic, message FROM sensor_data ORDER BY id DESC")
            rows = cursor.fetchall()
            conn.close()

            self.table.setRowCount(len(rows))
            for row_idx, row_data in enumerate(rows):
                for col_idx, col_data in enumerate(row_data):
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(col_data)))
        except Exception as e:
            print(f"Error loading data: {e}")

    def update_relay_status(self, status):
        """Update the relay status label."""
        if status == "ON":
            self.relay_status.setText("Relay Status: ON")
            self.relay_status.setStyleSheet("font-size: 16px; color: green;")
        else:
            self.relay_status.setText("Relay Status: OFF")
            self.relay_status.setStyleSheet("font-size: 16px; color: red;")

    def update_alert_status(self, alert_message):
        """Update the alert status label."""
        self.alert_status.setText(alert_message)
        if "Critical" in alert_message or "Low weight" in alert_message:
            self.alert_status.setStyleSheet("font-size: 16px; color: orange;")
        else:
            self.alert_status.setStyleSheet("font-size: 16px; color: blue;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = MainGUI()
    gui.show()
    sys.exit(app.exec_())
