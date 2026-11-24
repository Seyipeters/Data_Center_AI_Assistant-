
import os
import time
from datetime import datetime, timezone

import firebase_admin
from firebase_admin import credentials, db
from briefing import build_briefing, save_briefing


# Connect to Firebase
def connect_firebase():
    firebase_admin.initialize_app(
        credentials.ApplicationDefault(),
        {
            "databaseURL": os.environ["FIREBASE_DATABASE_URL"]
        }
    )

    print("Firebase connection established.")
    return db.reference("/current")


# Retrieve the latest reading
def get_reading(reference):
    data = reference.get()

    if not data:
        print("WARNING: No data received from Firebase.")
        return None

    return data


# Check whether the reading is outdated
def check_data_freshness(data):
    timestamp = datetime.fromisoformat(data["timestamp"])
    current_time = datetime.now(timezone.utc)

    age = (current_time - timestamp).total_seconds()

    if age > 30:
        print(f"WARNING: Stale data ({age:.1f} seconds old).")
        return False

    return True


# Detect environmental anomalies
def check_environment(data):
    environment = data["environment"]
    alerts = []

    temperature = environment["temperature_c"]
    humidity = environment["humidity_percent"]

    if temperature > 32:
        alerts.append(f"CRITICAL: Room overheating: {temperature} C")

    elif temperature > 27:
        alerts.append(f"WARNING: High room temperature: {temperature} C")

    elif temperature < 10:
        alerts.append(f"CRITICAL: Extremely low room temperature: {temperature} C")

    elif temperature < 18:
        alerts.append(f"WARNING: Low room temperature: {temperature} C")

    if humidity > 60:
        alerts.append(f"WARNING: High humidity: {humidity}%")

    elif humidity < 30:
        alerts.append(f"WARNING: Low humidity: {humidity}%")

    if environment["smoke_detected"]:
        alerts.append("CRITICAL: Smoke detected!")

    if environment["fire_detected"]:
        alerts.append("CRITICAL: Fire detected!")

    if environment["power_status"] != "normal":
        alerts.append("CRITICAL: Abnormal power supply!")

    return alerts


# Detect individual server anomalies
def check_servers(data):
    alerts = []

    for name, server in data["servers"].items():

        cpu = server["cpu_usage_percent"]
        memory = server["memory_usage_percent"]
        cpu_temp = server["cpu_temperature_c"]

        storage = server["storage"]
        disk_usage = storage["disk_usage_percent"]
        disk_health = storage["disk_health"]
        disk_temp = storage["disk_temperature_c"]

        latency = server["network"]["latency_ms"]

        if cpu >= 90:
            alerts.append(f"WARNING: {name} high CPU usage: {cpu}%")

        if memory >= 90:
            alerts.append(f"WARNING: {name} high memory usage: {memory}%")

        if cpu_temp >= 90:
            alerts.append(f"CRITICAL: {name} CPU overheating: {cpu_temp} C")

        elif cpu_temp >= 80:
            alerts.append(f"WARNING: {name} high CPU temperature: {cpu_temp} C")

        if disk_usage >= 95:
            alerts.append(f"CRITICAL: {name} disk usage: {disk_usage}%")

        elif disk_usage >= 80:
            alerts.append(f"WARNING: {name} disk usage: {disk_usage}%")

        if disk_health != "healthy":
            alerts.append(f"CRITICAL: {name} disk health: {disk_health}")

        if disk_temp >= 50:
            alerts.append(f"WARNING: {name} high disk temperature: {disk_temp} C")

        if latency >= 100:
            alerts.append(f"WARNING: {name} high network latency: {latency} ms")

    return alerts


# Main monitoring loop
def main():

    reference = connect_firebase()

    print("Data Center AI Assistant started.")
    print("Monitoring interval: 5 seconds")

    try:
        while True:

            try:
                data = get_reading(reference)

                if data and check_data_freshness(data):

                    alerts = check_environment(data)
                    alerts.extend(check_servers(data))

                    # Prioritise critical alerts
                    alerts.sort(
                        key=lambda alert: not alert.startswith("CRITICAL")
                    )

                    # Generate and save system briefing
                    briefing = build_briefing(
                        data, alerts, data_fresh=True
                    )

                    save_briefing(briefing)

                    # Display monitoring results
                    print("\n" + "=" * 50)
                    print("DATA CENTER MONITOR")
                    print("=" * 50)

                    print("Timestamp:", data["timestamp"])
                    print("Scenario:", data["scenario"])

                    print(
                        "Room temperature:",
                        data["environment"]["temperature_c"], "C"
                    )

                    print(
                        "Humidity:",
                        data["environment"]["humidity_percent"], "%"
                    )

                    if alerts:
                        print("\nACTIVE ALERTS:")

                        for alert in alerts:
                            print(alert)

                    else:
                        print("\nSTATUS: NORMAL")
                        print("No anomalies detected.")

                else:
                    # Handle stale or missing data
                    briefing = build_briefing(
                        data, [], data_fresh=False
                    )

                    save_briefing(briefing)

                    print("\nSTATUS: UNKNOWN")
                    print("Data is outdated or unavailable.")

            except Exception as error:

                print("MONITORING ERROR:", error)

                # Handle monitoring or Firebase errors
                try:
                    briefing = build_briefing(
                        None, [], data_fresh=False
                    )

                    save_briefing(briefing)

                except Exception as briefing_error:
                    print("BRIEFING ERROR:", briefing_error)

            time.sleep(5)

    except KeyboardInterrupt:
        print("\nMonitoring stopped.")


if __name__ == "__main__":
    main()
