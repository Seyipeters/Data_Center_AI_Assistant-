import unittest

from main import Simulator, upload_reading


class FakeReadingReference:
    key = 'reading-key'


class FakeReadingsReference:
    def push(self):
        return FakeReadingReference()


class FakeFirebaseRoot:
    def __init__(self):
        self.updated_values = None

    def child(self, path):
        if path != 'history':
            raise AssertionError(f'Unexpected child path: {path}')
        return FakeReadingsReference()

    def update(self, values):
        self.updated_values = values


class FirebaseUploadTests(unittest.TestCase):
    def test_upload_appends_history_and_updates_current_atomically(self):
        firebase_root = FakeFirebaseRoot()
        reading = {'timestamp': '2026-11-02T10:00:00+00:00'}
        upload_reading(firebase_root, reading)
        self.assertEqual(firebase_root.updated_values, {
            'history/reading-key': reading,
            'current': reading,
        })


class SimulatorScenarioTests(unittest.TestCase):
    def test_normal_temperature_stays_within_15_to_20(self):
        simulator = Simulator(seed=1)
        self.assertEqual(simulator.room_temp, 17.5)
        temperatures = [simulator.step()['environment']['temperature_c'] for _ in range(1000)]
        self.assertGreaterEqual(min(temperatures), 15.0)
        self.assertLessEqual(max(temperatures), 20.0)

    def test_custom_normal_temperature_bounds(self):
        simulator = Simulator(seed=2, temp_min=16, temp_max=19)
        temperatures = [simulator.step()['environment']['temperature_c'] for _ in range(300)]
        self.assertGreaterEqual(min(temperatures), 16)
        self.assertLessEqual(max(temperatures), 19)

    def test_overheating_increases_without_resetting_to_normal(self):
        simulator = Simulator('overheating', seed=1)
        temps = [simulator.step()['environment']['temperature_c'] for _ in range(20)]
        self.assertTrue(all(b >= a for a, b in zip(temps, temps[1:])))
        self.assertGreater(temps[-1], 20)
        self.assertLessEqual(temps[-1], 35)

    def test_fire_temperature_rises_and_fire_detection_is_delayed(self):
        simulator = Simulator('fire', seed=1)
        readings = [simulator.step() for _ in range(8)]
        self.assertFalse(readings[3]['environment']['fire_detected'])
        self.assertTrue(readings[4]['environment']['fire_detected'])
        self.assertTrue(readings[2]['environment']['smoke_detected'])
        temps = [r['environment']['temperature_c'] for r in readings]
        self.assertTrue(all(b >= a for a, b in zip(temps, temps[1:])))

    def test_disk_full(self):
        storage = Simulator('disk_full', seed=1).step()['servers']['server_03']['storage']
        self.assertEqual(storage['disk_usage_percent'], 100.0)
        self.assertEqual(storage['disk_free_gb'], 0)

    def test_high_server_temperature(self):
        reading = Simulator('high_server_temperature', seed=1).step()
        self.assertEqual(reading['servers']['server_03']['cpu_temperature_c'], 95.0)
        self.assertLess(reading['servers']['server_01']['cpu_temperature_c'], 95.0)


if __name__ == '__main__':
    unittest.main()
