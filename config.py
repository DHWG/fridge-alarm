import os
import logging

MQTT_BROKER = os.environ.get('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.environ.get('MQTT_PORT', '1883'))

ALERT_TIMEOUT = float(os.environ.get('ALERT_TIMEOUT', '5'))

MONITORED_SENSORS = os.environ.get('MONITORED_SENSORS', 'left_top').split()

TELEGRAM_CHAT_ID = int(os.environ.get('TELEGRAM_CHAT_ID', '0'))

LOGGING_LEVEL = logging.DEBUG