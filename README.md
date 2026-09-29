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
2. The data is uploaded to Firebase Realtime Database.
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
