import argparse
import json
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).parent / 'data'
SERVERS = ('server_01', 'server_02', 'server_03')
NORMAL_TEMP_MIN_C = 15.0
NORMAL_TEMP_MAX_C = 20.0
INITIAL_TEMP_C = 17.5


def clamp(value, low, high):
    return max(low, min(high, value))


class Simulator:
    def __init__(self, scenario='normal', seed=None, temp_min=NORMAL_TEMP_MIN_C,
                 temp_max=NORMAL_TEMP_MAX_C):
        if temp_min >= temp_max:
            raise ValueError('temp_min must be lower than temp_max')
        self.rng = random.Random(seed)
        self.scenario = scenario
        self.tick = 0
        self.temp_min = temp_min
        self.temp_max = temp_max
        self.room_temp = (temp_min + temp_max) / 2
        self.humidity = 45.0
        self.servers = {
            name: {'cpu': 35.0 + i * 6, 'memory': 48.0 + i * 5,
                   'disk_used_gb': 1000.0 + i * 100, 'disk_temp': 35.0}
            for i, name in enumerate(SERVERS)
        }

    def step(self):
        self.tick += 1
        r = self.rng
        if self.scenario == 'overheating':
            self.room_temp = min(self.room_temp + 0.6, 35.0)
        elif self.scenario == 'fire':
            self.room_temp = min(self.room_temp + (2.5 if self.tick >= 5 else 0.3), 80.0)
        else:
            self.room_temp = clamp(self.room_temp + r.uniform(-0.25, 0.25),
                                   self.temp_min, self.temp_max)
        self.humidity = clamp(self.humidity + r.uniform(-0.6, 0.6), 30, 65)
        smoke = self.scenario in ('smoke', 'fire') and self.tick >= 3
        fire = self.scenario == 'fire' and self.tick >= 5
        if self.scenario == 'high_humidity':
            self.humidity = clamp(self.humidity + 2.5, 0, 100)
        environment = {
            'temperature_c': round(self.room_temp, 1),
            'humidity_percent': round(self.humidity, 1),
            'smoke_detected': smoke,
            'fire_detected': fire,
            'power_status': 'outage' if self.scenario == 'power_failure' and self.tick >= 3 else 'normal'
        }
        servers = {}
        for name, state in self.servers.items():
            state['cpu'] = clamp(state['cpu'] + r.uniform(-5, 5), 5, 95)
            state['memory'] = clamp(state['memory'] + r.uniform(-1.5, 1.5), 10, 95)
            state['disk_temp'] = clamp(state['disk_temp'] + r.uniform(-0.4, 0.4), 25, 55)
            state['disk_used_gb'] = clamp(state['disk_used_gb'] + r.uniform(0.01, 0.2), 0, 2000)
            if name == 'server_03' and self.scenario == 'storage_full':
                state['disk_used_gb'] = clamp(state['disk_used_gb'] + 100, 0, 2000)
            if name == 'server_03' and self.scenario == 'disk_full':
                state['disk_used_gb'] = 2000
            disk_health = ('failing' if name == 'server_03' and
                           self.scenario == 'storage_failure' and self.tick >= 4
                           else 'healthy')
            used = round(state['disk_used_gb'], 2)
            cpu_temperature = (95.0 if name == 'server_03' and
                               self.scenario == 'high_server_temperature'
                               else round(37 + state['cpu'] * 0.45, 1))
            servers[name] = {
                'cpu_usage_percent': round(state['cpu'], 1),
                'memory_usage_percent': round(state['memory'], 1),
                'cpu_temperature_c': cpu_temperature,
                'storage': {
                    'disk_total_gb': 2000,
                    'disk_used_gb': used,
                    'disk_free_gb': round(2000 - used, 2),
                    'disk_usage_percent': round(used / 20, 2),
                    'disk_temperature_c': round(state['disk_temp'], 1),
                    'disk_health': disk_health,
                },
                'network': {'latency_ms': round(r.uniform(5, 25), 1)}
            }
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'simulated': True,
            'scenario': self.scenario,
            'environment': environment,
            'servers': servers
        }


def save_reading(reading):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / 'current.json').write_text(json.dumps(reading, indent=2), encoding='utf-8')
    with (DATA_DIR / 'history.jsonl').open('a', encoding='utf-8') as file:
        file.write(json.dumps(reading) + '\n')


def initialize_firebase(database_url):
    from firebase_admin import credentials, db, initialize_app

    app = initialize_app(credentials.ApplicationDefault(), {'databaseURL': database_url})
    return db.reference('/', app=app)


def upload_reading(firebase_root, reading):
    reading_key = firebase_root.child('history').push().key
    if reading_key is None:
        raise RuntimeError('Firebase did not generate a key for the reading')
    firebase_root.update({f'history/{reading_key}': reading, 'current': reading})


def main():
    parser = argparse.ArgumentParser(description='Data center monitoring simulator')
    parser.add_argument('--interval', type=float, default=60, help='Seconds between readings')
    parser.add_argument('--count', type=int, default=0, help='Number of readings; 0 runs continuously')
    parser.add_argument('--temp-min', type=float, default=NORMAL_TEMP_MIN_C,
                        help='Normal room temperature minimum in Celsius (default: 15)')
    parser.add_argument('--temp-max', type=float, default=NORMAL_TEMP_MAX_C,
                        help='Normal room temperature maximum in Celsius (default: 20)')
    parser.add_argument('--scenario', choices=[
        'normal', 'overheating', 'high_server_temperature', 'high_humidity',
        'smoke', 'fire', 'power_failure', 'storage_full', 'disk_full', 'storage_failure'
    ], default='normal')
    parser.add_argument('--seed', type=int, default=None)
    args = parser.parse_args()
    if args.interval <= 0 or args.count < 0 or args.temp_min >= args.temp_max:
        parser.error('interval must be positive, count nonnegative, and temp-min lower than temp-max')
    simulator = Simulator(args.scenario, args.seed, args.temp_min, args.temp_max)
    database_url = os.getenv('FIREBASE_DATABASE_URL')
    firebase_root = initialize_firebase(database_url) if database_url else None
    try:
        while args.count == 0 or simulator.tick < args.count:
            reading = simulator.step()
            save_reading(reading)
            if firebase_root is not None:
                upload_reading(firebase_root, reading)
            print(json.dumps(reading, indent=2), flush=True)
            if args.count == 0 or simulator.tick < args.count:
                time.sleep(args.interval)
    except KeyboardInterrupt:
        print('\nSimulator stopped.')


if __name__ == '__main__':
    main()
