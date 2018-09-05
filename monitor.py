#!/usr/bin/env python3

import json
import time
import threading
import logging
import config
import paho.mqtt.client as mqtt


class SensorMonitor:

    def __init__(self):
        self._last_update = {}
        self._last_state = {}
        self._callbacks = {}
        self._monitors = {}
        self._triggered = {}
        self._logger = logging.getLogger(__class__.__name__)
    
    def update(self, sensor, state):
        """Updates the state for a sensor.
        
        Arguments
        ---------
        sensor : str
            The ID of the sensor
        state : anything
            The state of the sensor"""
        self._logger.debug(f'Updating state for {sensor} to {state}')
        last_state = self._last_state.get(sensor, None)
        self._last_update[sensor] = time.time()
        self._last_state[sensor] = state
        if not state == last_state:
            callbacks = self._callbacks.get(sensor, [])
            self._logger.debug(f'Calling {len(callbacks)} callbacks for {sensor}')
            for callback in callbacks:
                callback(sensor, last_state, state)
    
    def __getitem__(self, sensor):
        """Access the last state for a sensor.

        Arguments
        ---------
        sensor : str
            The ID of the sensor
        
        Returns
        -------
        state : anything
            Last known state
        updated : float
            Timestamp of the last update"""
        if not (sensor in self._last_update and sensor in self._last_state):
            raise KeyError(sensor)
        state = self._last_state[sensor]
        updated = self._last_update[sensor]
        return state, updated

    def add_callback(self, sensor, callback):
        """Register a callback that will be called when the state of a sensor changes.
        
        Arguments
        ---------
        sensor : str
            ID of the sensor
        callback: Callable[[str, anything, anything], None]
            Signatur is (sensor ID, old value, new value)"""
        callback_list = self._callbacks.setdefault(sensor, [])
        callback_list.append(callback)
    
    def set_alert(self, sensor, alert_state, timeout, alert_triggered_callback=None, alert_resolved_callback=None):
        """Sets an alert for a sensor.
        Alerts are triggered if a certain value is reported for a certain amount of time.
        
        Arguments
        ---------
        sensor : str
            ID of the sensor
        alert_state : anything
            The state that will trigger an alert
        timeout : float
            Number of seconds after which the alert will be triggered
        alert_triggered_callback : Callable[[str, anything], None]
            Callback for when the alert is triggered. Signature: sensor ID, current state
        alert_resolved_callback : Callable[[str, anything], None]
            Callback for when the alert is resolved. Signature: sensor ID, current state
        """
        self._logger.info(f'Setting alert for {sensor} on state {alert_state} after {timeout}s')
        def _state_change_callback(sensor, old_state, new_state):
            if new_state == alert_state:
                def check_state_func():
                    state, _ = self[sensor]
                    if state == alert_state:
                        self._logger.info(f'Alert triggered for {sensor} because state {alert_state} for {timeout}s')
                        self._triggered[sensor] = True
                        if alert_triggered_callback is not None:
                            alert_triggered_callback(sensor, new_state)
                monitor = threading.Timer(timeout, check_state_func)
                monitor.start()
                self._monitors[sensor] = monitor
            else:
                if sensor in self._monitors:
                    self._monitors[sensor].cancel()
                if self._triggered.get(sensor, False):
                    self._logger.info(f'Alert resolved for {sensor} because state {new_state}')
                    if alert_resolved_callback is not None:
                        alert_resolved_callback(sensor, new_state)
                    self._triggered[sensor] = False
        self.add_callback(sensor, _state_change_callback)


def send_to_billy(msg, mqtt_client):
    mqtt_client.publish('billy/speak', msg.encode('utf8'))

def send_to_telegram(msg, mqtt_client):
    telegram_cmd = {
        'command': 'sendMessage',
        'payload': {
            'chat_id': config.TELEGRAM_CHAT_ID,
            'text': msg
        }
    }
    mqtt_client.publish('chat/outgoing', json.dumps(telegram_cmd).encode('utf8'))


if __name__ == '__main__':
    logging.basicConfig(level=config.LOGGING_LEVEL)

    NAME_MAPPING = {
        'left_bottom': 'left freezer',
        'left_top': 'left fridge',
        'right_bottom': 'right freezer',
        'right_top': 'right fridge',
        'beer': 'community fridge'
    }

    monitor = SensorMonitor()

    def on_mqtt_connect(client, userdata, flags, rc):
        print('Connected with result code ' + str(rc))
        client.subscribe('devices/fridges')

    def on_mqtt_message(client, userdata, msg):
        data = json.loads(msg.payload)
        for sensor in config.MONITORED_SENSORS:
            monitor.update(sensor, data[sensor])

    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_mqtt_connect
    mqtt_client.on_message = on_mqtt_message

    def trigger_alert(sensor, state):
        chat_msg = '{} has been open for more than {} seconds.'.format(NAME_MAPPING.get(sensor),
                                                                       config.ALERT_TIMEOUT)
        send_to_telegram(chat_msg, mqtt_client)
        fish_msg = 'Close the {} you dunce.'.format(NAME_MAPPING.get(sensor))
        send_to_billy(fish_msg, mqtt_client)
    
    def resolve_alert(sensor, state):
        chat_msg = '{} has been closed again.'.format(NAME_MAPPING.get(sensor))
        send_to_telegram(chat_msg, mqtt_client)
        fish_msg = 'Thank you for closing {}.'.format(NAME_MAPPING.get(sensor))
        send_to_billy(fish_msg, mqtt_client)
    
    for sensor in config.MONITORED_SENSORS:
        monitor.set_alert(sensor,
                          alert_state=1,
                          timeout=config.ALERT_TIMEOUT,
                          alert_triggered_callback=trigger_alert,
                          alert_resolved_callback=resolve_alert)

    mqtt_client.connect(config.MQTT_BROKER, config.MQTT_PORT, 60)
    mqtt_client.loop_forever()
