# This is executed after boot.py

import time
import ubinascii
import machine
import config
from umqtt.simple import MQTTClient
import ujson

D0 = const(16)
D1 = const(5)
D2 = const(4)
D3 = const(0)
D4 = const(2)
D5 = const(14)
D6 = const(12)
D7 = const(13)
D8 = const(15)
D9 = const(3)
D10 = const(1)

MQTT_CID = b'esp-' + ubinascii.hexlify(machine.unique_id())

mqtt = MQTTClient(MQTT_CID, config.MQTT_HOST)

pin_1 = machine.Pin(D1, machine.Pin.IN, machine.Pin.PULL_UP)
pin_2 = machine.Pin(D2, machine.Pin.IN, machine.Pin.PULL_UP)
pin_3 = machine.Pin(D3, machine.Pin.IN, machine.Pin.PULL_UP)
pin_4 = machine.Pin(D4, machine.Pin.IN, machine.Pin.PULL_UP)
pin_5 = machine.Pin(D5, machine.Pin.IN, machine.Pin.PULL_UP)

def mqtt_callback(topic, message):
    # called when a new MQTT message arrives
    pass

def cycle():
    data = {
        'left_top': pin_1.value(),
        'left_bottom': pin_2.value(),
        'right_top': pin_3.value(),
        'right_bottom': pin_4.value(),
        'beer': pin_5.value()
    }
    # read inputs of the chip etc
    mqtt.publish(b'devices/fridges', ujson.dumps(data))


if __name__ == '__main__':
    print('Running main loop.')
    mqtt.set_callback(mqtt_callback)
    mqtt.connect()
    try:
        while 1:
            cycle()
            mqtt.check_msg()
            time.sleep_ms(1000)
    finally:
        mqtt.disconnect()

