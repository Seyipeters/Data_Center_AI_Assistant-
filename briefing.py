from datetime import datetime, timezone


# Determine overall system status
def get_system_status(alerts, data_fresh=True):

    if not data_fresh:
        return "UNKNOWN"

    if any(alert.startswith("CRITICAL") for alert in alerts):
        return "CRITICAL"

    if any(alert.startswith("WARNING") for alert in alerts):
        return "WARNING"

    return "NORMAL"


# Build a structured system briefing
def build_briefing(data, alerts, data_fresh):

    status = get_system_status(alerts, data_fresh)

    briefing = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "reading_timestamp": None,
        "status": status,
        "data_fresh": data_fresh,
        "simulated": None,
        "environment": {},
        "servers": {},
        "server_count": 0,
        "alert_count": len(alerts),
        "alerts": alerts
    }

    if data:
        briefing["reading_timestamp"] = data.get("timestamp")
        briefing["simulated"] = data.get("simulated")
        briefing["environment"] = data.get("environment", {})
        briefing["servers"] = data.get("servers", {})
        briefing["server_count"] = len(briefing["servers"])

    return briefing


# Generate a human-readable summary
def generate_summary(briefing):

    status = briefing["status"]
    alerts = briefing["alerts"]
    server_count = briefing["server_count"]

    if status == "UNKNOWN":
        return (
            "Current system health cannot be confirmed. "
            "Data is outdated or unavailable."
        )

    if status == "NORMAL":
        return (
            f"All {server_count} monitored servers are operating "
            "within configured limits. "
            "No anomalies have been detected."
        )

    summary = (
        f"System status is {status}. "
        f"{len(alerts)} active alerts detected. "
    )

    summary += " ".join(alerts)

    return summary


# Generate recommended actions
def recommend_action(briefing):

    status = briefing["status"]

    if status == "UNKNOWN":
        return "Check the simulator, network and Firebase connection."

    if status == "CRITICAL":
        return "Notify the operator and investigate critical alerts immediately."

    if status == "WARNING":
        return "Investigate abnormal readings and monitor affected systems."

    return "Continue routine monitoring."


# Export the system briefing to a JSON file
def save_briefing(briefing):

    import json
    from pathlib import Path

    briefing["summary"] = generate_summary(briefing)
    briefing["recommended_action"] = recommend_action(briefing)

    directory = Path(__file__).resolve().parent / "data"
    directory.mkdir(parents=True, exist_ok=True)

    file_path = directory / "briefing.json"
    temp_path = directory / "briefing.tmp"

    with temp_path.open("w", encoding="utf-8") as file:
        json.dump(briefing, file, indent=4)

    temp_path.replace(file_path)

    return file_path
