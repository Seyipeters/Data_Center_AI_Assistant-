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
        if path != 'readings':
            raise AssertionError(f'Unexpected child path: {path}')
        return FakeReadingsReference()

    def update(self, values):
        self.updated_values = values


class FirebaseUploadTests(unittest.TestCase):
    def test_upload_appends_reading_and_updates_current_atomically(self):
        firebase_root = FakeFirebaseRoot()
        reading = {'timestamp': '2026-11-02T10:00:00+00:00'}

        upload_reading(firebase_root, reading)

        self.assertEqual(firebase_root.updated_values, {
            'readings/reading-key': reading,
            'current': reading,
        })


class SimulatorScenarioTests(unittest.TestCase):
    def test_normal_room_temperature_stays_cool(self):
        simulator = Simulator(seed=1)

        temperatures = [
            simulator.step()['environment']['temperature_c']
            for _ in range(100)
        ]

        self.assertGreaterEqual(min(temperatures), 17.0)
        self.assertLessEqual(max(temperatures), 21.0)

    def test_overheating_scenario_rises_above_normal_room_temperature(self):
        simulator = Simulator('overheating', seed=1)

        readings = [simulator.step() for _ in range(5)]

        self.assertGreater(readings[-1]['environment']['temperature_c'], 21.0)

    def test_disk_full_scenario_reports_server_three_at_capacity(self):
        reading = Simulator('disk_full', seed=1).step()
        storage = reading['servers']['server_03']['storage']

        self.assertEqual(storage['disk_usage_percent'], 100.0)
        self.assertEqual(storage['disk_free_gb'], 0)

    def test_high_server_temperature_scenario_reports_abnormal_cpu_temperature(self):
        reading = Simulator('high_server_temperature', seed=1).step()

        self.assertEqual(reading['servers']['server_03']['cpu_temperature_c'], 95.0)
        self.assertLess(reading['servers']['server_01']['cpu_temperature_c'], 95.0)


if __name__ == '__main__':
    unittest.main()
