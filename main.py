import argparse
import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).parent / 'data'
SERVERS = ('server_01', 'server_02', 'server_03')


def clamp(value, low, high):
    return max(low, min(high, value))


class Simulator:
    def __init__(self, scenario='normal', seed=None):
        self.rng = random.Random(seed)
        self.scenario = scenario
        self.tick = 0
        self.room_temp = 22.0
        self.humidity = 45.0
        self.servers = {
            name: {'cpu': 35.0 + i * 6, 'memory': 48.0 + i * 5,
                   'disk_used_gb': 1000.0 + i * 100, 'disk_temp': 35.0}
            for i, name in enumerate(SERVERS)
        }

    def step(self):
        self.tick += 1
        r = self.rng
        self.room_temp = clamp(self.room_temp + r.uniform(-0.25, 0.25), 19, 27)
        self.humidity = clamp(self.humidity + r.uniform(-0.6, 0.6), 30, 65)
        smoke = self.scenario in ('smoke', 'fire') and self.tick >= 3
        fire = self.scenario == 'fire' and self.tick >= 5
        if self.scenario == 'overheating':
            self.room_temp += self.tick * 0.4
        if self.scenario == 'fire':
            self.room_temp += (2.5 if fire else 0.3)
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
            if name == 'server_03' and self.scenario == 'storage_failure' and self.tick >= 4:
                disk_health = 'failing'
            else:
                disk_health = 'healthy'
            used = round(state['disk_used_gb'], 2)
            servers[name] = {
                'cpu_usage_percent': round(state['cpu'], 1),
                'memory_usage_percent': round(state['memory'], 1),
                'cpu_temperature_c': round(37 + state['cpu'] * 0.45, 1),
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


def main():
    parser = argparse.ArgumentParser(description='Data center monitoring simulator')
    parser.add_argument('--interval', type=float, default=60, help='Seconds between readings')
    parser.add_argument('--count', type=int, default=0, help='Number of readings; 0 runs continuously')
    parser.add_argument('--scenario', choices=['normal', 'overheating', 'high_humidity', 'smoke', 'fire', 'power_failure', 'storage_full', 'storage_failure'], default='normal')
    parser.add_argument('--seed', type=int, default=None)
    args = parser.parse_args()
    if args.interval <= 0 or args.count < 0:
        parser.error('--interval must be positive and --count must be nonnegative')
    simulator = Simulator(args.scenario, args.seed)
    try:
        while args.count == 0 or simulator.tick < args.count:
            reading = simulator.step()
            save_reading(reading)
            print(json.dumps(reading, indent=2), flush=True)
            if args.count == 0 or simulator.tick < args.count:
                time.sleep(args.interval)
    except KeyboardInterrupt:
        print('\nSimulator stopped.')


if __name__ == '__main__':
    main()
