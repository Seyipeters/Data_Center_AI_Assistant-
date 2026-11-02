# Data Center AI Assistant

A proactive desk assistant that helps server operators monitor data center conditions without needing to perform routine manual checks in the server room.

The system generates simulated server room data using Python, stores it in Firebase, and uses a Raspberry Pi with an e-ink display and voice assistant to provide updates and alerts.

## Key Features

- **Morning briefing:** Provides a summary of server room conditions at a scheduled time, such as 8:00 or 9:00 a.m.
- **Continuous monitoring:** Checks incoming data throughout the day.
- **Proactive alerts:** Notifies the operator when an anomaly or significant change is detected.
- **E-ink display:** Shows current readings, system status, and alerts.
- **Voice assistant:** Provides spoken updates and answers questions about monitoring data.
- **AI-assisted insights:** Explains detected conditions and summarizes available data.

## How It Works

1. Python generates simulated server room readings.
2. The data is saved locally and, when Firebase is configured, uploaded to Firebase Realtime Database.
3. The Raspberry Pi continuously retrieves updated data.
4. Monitoring logic checks for abnormal readings and changes.
5. The e-ink display updates with the latest status.
6. The assistant provides a scheduled morning briefing and proactive alerts during the day.

```text
Python Data Simulator
        ↓
Firebase Realtime Database
        ↓
Raspberry Pi
        ↓
Monitoring and Anomaly Detection
        ↓
E-ink Display + Voice Assistant
```

## Running the Simulator with Firebase

The simulator always saves readings to `data/current.json` and `data/history.jsonl`.
To also upload readings, configure a Firebase Realtime Database and a service
account credential with write access. Keep the service account JSON out of the
repository.

In PowerShell, set the database URL from the Firebase console and point the
Google Application Default Credentials environment variable at your service
account JSON:

```powershell
$env:FIREBASE_DATABASE_URL = "https://<your-database-url>"
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\path\to\service-account.json"
python main.py --interval 10 --count 5
```

When `FIREBASE_DATABASE_URL` is set, each reading is written to
`/readings/{push-id}` and `/current` is updated with the latest reading. If
Firebase is not configured, the simulator runs locally as before. Firebase
connection or upload errors are reported and stop the simulator.

## Simulator Scenarios

Normal room-temperature readings start at 18 °C and fluctuate within 17–21 °C.
The `overheating` and `fire` scenarios intentionally raise the room temperature
above this normal range.

Pass `--scenario` to generate abnormal readings. Available scenarios include:

- `overheating`: gradually raises room temperature.
- `high_server_temperature`: sets server_03's CPU temperature to 95 °C.
- `high_humidity`: raises room humidity.
- `smoke` and `fire`: simulate smoke, with fire detected after several readings.
- `power_failure`: simulates a power outage after several readings.
- `storage_full`: gradually fills server_03's disk.
- `disk_full`: sets server_03's disk usage to 100% immediately.
- `storage_failure`: marks server_03's disk as failing after several readings.

For example, run a single reading showing a full disk:

```powershell
python main.py --scenario disk_full --count 1
```

Or run the high server temperature scenario:

```powershell
python main.py --scenario high_server_temperature --count 1
```
