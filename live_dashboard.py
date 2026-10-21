import json
import threading
from datetime import datetime

import pandas as pd
import paho.mqtt.client as mqtt
import streamlit as st
from streamlit_autorefresh import st_autorefresh

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "transformer-demo-ice-2026/sensor-data"

st.set_page_config(
    page_title="Transformer Health Monitoring",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Smart Transformer Health Monitoring")
st.caption("Live MQTT sensor monitoring and predictive maintenance")

# Shared data store and MQTT connection
@st.cache_resource
def start_mqtt():
    store = {
        "latest": None,
        "history": []
    }
    lock = threading.Lock()

    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            client.subscribe(TOPIC)

    def on_message(client, userdata, message):
        try:
            data = json.loads(message.payload.decode())

            reading = {
                "Time": datetime.now(),
                "Temperature": float(data.get("temperature", 0)),
                "Vibration": float(data.get("vibration", 0)),
                "Turbidity": float(data.get("turbidity", 0)),
                "Gas": float(data.get("gas", 0))
            }

            with lock:
                store["latest"] = reading
                store["history"].append(reading.copy())
                store["history"] = store["history"][-100:]

        except (ValueError, TypeError, json.JSONDecodeError):
            pass

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="streamlit-transformer-dashboard"
    )
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(BROKER, PORT, 60)
        client.loop_start()
    except Exception as error:
        store["error"] = str(error)

    return store, lock

store, lock = start_mqtt()

# Refresh dashboard every 2 seconds
st_autorefresh(interval=2000, key="mqtt_refresh")

with lock:
    data = store["latest"]
    history = list(store["history"])

if data is None:
    st.info("Waiting for MQTT readings from Wokwi...")
    st.write("Make sure your Wokwi simulation is running.")
    if store.get("error"):
        st.error("MQTT connection error: " + store["error"])
    st.stop()

temperature = data["Temperature"]
vibration = data["Vibration"]
turbidity = data["Turbidity"]
gas = data["Gas"]

st.subheader("Live Sensor Readings")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Oil Temperature", f"{temperature:.1f} °C")
c2.metric("Vibration", f"{vibration:.1f} %")
c3.metric("Oil Turbidity", f"{turbidity:.1f} %")
c4.metric("Gas Level", f"{gas:.1f} %")

st.subheader("Transformer Condition")

if temperature >= 90 or vibration >= 80 or gas >= 80:
    st.error("CRITICAL: Abnormal readings detected")
    health = "Critical"
elif temperature >= 70 or vibration >= 50 or gas >= 50 or turbidity >= 70:
    st.warning("WARNING: Check transformer condition")
    health = "Warning"
else:
    st.success("NORMAL: Readings are within demo limits")
    health = "Normal"

st.write("Current demo status:", health)

# Demonstration-only health index
temp_risk = min(1.0, max(0.0, (temperature - 50) / 50))
vibration_risk = min(1.0, max(0.0, vibration / 100))
turbidity_risk = min(1.0, max(0.0, turbidity / 100))
gas_risk = min(1.0, max(0.0, gas / 100))

health_index = round(max(0, min(
    100,
    100 - (
        40 * temp_risk
        + 20 * vibration_risk
        + 15 * turbidity_risk
        + 25 * gas_risk
    )
)), 1)

st.metric("Demo Transformer Health Index", f"{health_index}/100")

st.subheader("Maintenance Recommendations")
recommendations = []

if temperature >= 70:
    recommendations.append("High temperature: inspect cooling and verify the sensor.")
if vibration >= 50:
    recommendations.append("High vibration: inspect mounting and mechanical looseness.")
if turbidity >= 70:
    recommendations.append("High turbidity: inspect oil condition and verify the sensor.")
if gas >= 50:
    recommendations.append("High gas reading: verify the sensor and arrange appropriate oil-gas analysis.")

if not recommendations:
    recommendations.append("No demo threshold exceeded. Continue monitoring.")

for item in recommendations:
    st.write("- " + item)

st.subheader("Sensor Overview")
chart = pd.DataFrame({
    "Parameter": ["Temperature", "Vibration", "Turbidity", "Gas"],
    "Value": [temperature, vibration, turbidity, gas]
}).set_index("Parameter")
st.bar_chart(chart)

st.subheader("📈 Live Sensor History")
if history:
    history_df = pd.DataFrame(history).set_index("Time")
    st.line_chart(history_df[["Temperature", "Vibration", "Turbidity", "Gas"]])
else:
    st.info("Collecting sensor history...")

st.caption(
    "Educational demo only. The health index and thresholds are not "
    "validated for real transformer protection or maintenance decisions."
)
