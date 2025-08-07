"""This is a fast-created script without optimizaion
to aquire the result.
"""


import csv
import json
import logging
from datetime import datetime, timezone
from collections import Counter
from xml.etree import ElementTree as ET
import Evtx.Evtx as evtx

EVTX_FILE = "W2022.evtx"
NAMESPACE = {'e': 'http://schemas.microsoft.com/win/2004/08/events/event'}

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

def parse_event(record):
    xml = ET.fromstring(record.xml())

    system = xml.find("e:System", NAMESPACE)
    if system is None:
        raise ValueError("Missing <System> element")

    event_id_text = system.findtext("e:EventID", default="", namespaces=NAMESPACE)
    event_id = int(event_id_text) if event_id_text.isdigit() else 0

    provider = system.find("e:Provider", NAMESPACE)
    provider_name = provider.attrib.get("Name", "") if provider is not None else ""

    time_node = system.find("e:TimeCreated", NAMESPACE)
    time_str = time_node.attrib.get("SystemTime") if time_node is not None else None
    timestamp = None
    if time_str:
        timestamp = datetime.fromisoformat(time_str.replace("Z", "+00:00"))

    level_text = system.findtext("e:Level", default="0", namespaces=NAMESPACE)
    level = int(level_text) if level_text.isdigit() else 0

    eventdata = xml.find("e:EventData", NAMESPACE)
    strings = []
    if eventdata is not None:
        strings = [data.text for data in eventdata.findall("e:Data", NAMESPACE) if data.text]

    message = "\n".join(strings)

    return {
        "event_id": event_id,
        "provider": provider_name,
        "timestamp": timestamp,
        "level": level,
        "strings": strings,
        "message": message,
    }

def guess_reason(event):
    if event is None:
        return "Unknown"
    if event["event_id"] == 6005:
        return "System startup"
    if event["event_id"] == 6006:
        return "System shutdown"
    if "power" in event["message"].lower():
        return "Power failure"
    return "Unknown"

def process_events(evtx_file, start_time, end_time):
    error_count = 0
    warning_count = 0
    scm_events_in_range = []
    stopped_services = Counter()
    uptime_events = []

    with evtx.Evtx(evtx_file) as log:
        for record in log.records():
            try:
                event = parse_event(record)

                if event["level"] == 2:
                    error_count += 1
                elif event["level"] == 3:
                    warning_count += 1

                if (event["provider"] == "Service Control Manager" and
                    event["timestamp"] is not None and
                    start_time <= event["timestamp"] <= end_time):
                    service_name = event["strings"][0] if event["strings"] else "Unknown"
                    scm_events_in_range.append({
                        "event_id": event["event_id"],
                        "timestamp": event["timestamp"].isoformat(),
                        "service_name": service_name,
                        "message": event["message"]
                    })

                if (event["provider"] == "Service Control Manager" and
                    "stopped" in event["message"].lower()):
                    service_name = event["strings"][0] if event["strings"] else "Unknown"
                    stopped_services[service_name] += 1

                if event["event_id"] in (6005, 6006) or "uptime" in event["message"].lower():
                    uptime_events.append(event)

            except Exception as e:
                logging.error(f"Error parsing record: {e}")

    return error_count, warning_count, scm_events_in_range, stopped_services, uptime_events

def output_results(error_count, warning_count, scm_events, stopped_services, uptime_events):
    logging.info("=== Task 1: Error and Warning counts ===")
    logging.info(f"Error events  : {error_count}")
    logging.info(f"Warning events: {warning_count}")

    logging.info("\n=== Task 2: SCM events between given timestamps ===")
    for e in scm_events:
        logging.info(f"[{e['timestamp']}] Event ID: {e['event_id']}, Service: {e['service_name']}")
        logging.info(f"Message: {e['message']}")
        logging.info("---")

    csv_file = "stopped_services_report.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Service Name", "Stop Count"])
        for service, count in stopped_services.items():
            writer.writerow([service, count])
    logging.info(f"Task 3: Stopped services report exported to {csv_file}")

    uptime_events_sorted = sorted(uptime_events, key=lambda e: e["timestamp"])
    current_uptime = uptime_events_sorted[-1] if uptime_events_sorted else None
    last_uptime = uptime_events_sorted[-2] if len(uptime_events_sorted) > 1 else None

    uptime_report = {
        "current_system_uptime": current_uptime["timestamp"].isoformat() if current_uptime else None,
        "last_logged_system_uptime": last_uptime["timestamp"].isoformat() if last_uptime else None,
        "most_likely_reason_for_current_uptime": guess_reason(current_uptime)
    }

    logging.info("\n=== Task 4: Uptime Report (JSON) ===")
    logging.info(json.dumps(uptime_report, indent=2))

def main():
    start_time = datetime(2025, 8, 1, 13, 37, 15, tzinfo=timezone.utc)
    end_time = datetime(2025, 8, 1, 13, 57, 43, tzinfo=timezone.utc)

    error_count, warning_count, scm_events, stopped_services, uptime_events = process_events(
        EVTX_FILE, start_time, end_time
    )

    output_results(error_count, warning_count, scm_events, stopped_services, uptime_events)

if __name__ == "__main__":
    main()
