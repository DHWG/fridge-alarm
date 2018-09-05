import unittest
import time
from monitor import SensorMonitor

class SensorMonitorTestCase(unittest.TestCase):

    def test_update_and_get(self):
        monitor = SensorMonitor()

        monitor.update('sensor1', 1)

        state, _ = monitor['sensor1']
        self.assertEquals(state, 1)
    
    def test_callback(self):
        monitor = SensorMonitor() 
        monitor.update('sensor1', 0)

        result_collector = {}

        def callback(sensor, old_value, new_value):
            result_collector[sensor] = '{}->{}'.format(old_value, new_value)
   
        monitor.add_callback('sensor1', callback)

        monitor.update('sensor1', 1)

        self.assertEquals(result_collector['sensor1'], '0->1')

    def test_alerting(self):
        # this is not 100% bullet-proof, but it should work well enough
        monitor = SensorMonitor()

        result_collector = {}

        def alert_triggered_callback(sensor, state):
            result_collector['triggered'] = True
        
        def alert_resolved_callback(sensor, state):
            result_collector['resolved'] = True
        
        monitor.set_alert('sensor1',
                          alert_state=1,
                          timeout=2,
                          alert_triggered_callback=alert_triggered_callback,
                          alert_resolved_callback=alert_resolved_callback)
        
        self.assertNotIn('triggered', result_collector)
        self.assertNotIn('resolved', result_collector)

        monitor.update('sensor1', 1)

        self.assertNotIn('triggered', result_collector)
        self.assertNotIn('resolved', result_collector)

        time.sleep(5)

        self.assertIn('triggered', result_collector)
        self.assertNotIn('resolved', result_collector)

        monitor.update('sensor1', 0)

        self.assertIn('triggered', result_collector)
        self.assertIn('resolved', result_collector)