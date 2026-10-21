import json
import os
import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="Transformer Health Monitoring",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Smart Transformer Health Monitoring")
st.caption("Live sensor monitoring and predictive maintenance")

# Refresh the dashboard every 2 seconds
st_autorefresh(interval=2000, key="refresh")
# Store sensor reading history
if "history" not in st.session_state:
    st.session_state.history = []

DATA_FILE = "latest_sensor_data.json"

if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r") as file:
            data = json.load(file)

        if data:
            temperature = float(data.get("temperature", 0))
            vibration = float(data.get("vibration", 0))
            turbidity = float(data.get("turbidity", 0))
            gas = float(data.get("gas", 0))
            # Demo Transformer Health Index
            temp_risk = min(1.0, max(0.0, (temperature - 50) / 50))
            vibration_risk = min(1.0, max(0.0, vibration / 100))
            turbidity_risk = min(1.0, max(0.0, turbidity / 100))
            gas_risk = min(1.0, max(0.0, gas / 100))

            health_index = 100 - (
                    40 * temp_risk
                    + 20 * vibration_risk
                    + 15 * turbidity_risk
                    + 25 * gas_risk
            )

            health_index = round(max(0, min(100, health_index)), 1)
            st.session_state.history.append({
                "Time": pd.Timestamp.now(),
                "Temperature": temperature,
                "Vibration": vibration,
                "Turbidity": turbidity,
                "Gas": gas
            })

            # Keep only the latest 100 readings
            st.session_state.history = st.session_state.history[-100:]

            st.subheader("Live Sensor Readings")

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Oil Temperature", f"{temperature:.1f} °C")
            col2.metric("Vibration", f"{vibration:.1f} %")
            col3.metric("Oil Turbidity", f"{turbidity:.1f} %")
            col4.metric("Gas Level", f"{gas:.1f} %")

            st.subheader("Transformer Condition")
            st.subheader("Maintenance Recommendations")

            recommendations = []

            if temperature >= 70:
                recommendations.append(
                    "High temperature: inspect cooling and verify the temperature sensor."
                )

            if vibration >= 50:
                recommendations.append(
                    "High vibration: inspect mounting, mechanical looseness, and vibration sensor."
                )

            if turbidity >= 70:
                recommendations.append(
                    "High oil turbidity: inspect oil condition and verify the sensor."
                )

            if gas >= 50:
                recommendations.append(
                    "High gas reading: verify the sensor and arrange appropriate oil-gas analysis."
                )

            if not recommendations:
                recommendations.append(
                    "No demo threshold exceeded. Continue monitoring the readings."
                )

            for item in recommendations:
                st.write("•", item)
            st.subheader("Transformer Health Index")
            st.metric("Health Score", f"{health_index}/100")

            if health_index >= 80:
                st.success("Good demo health score")
            elif health_index >= 50:
                st.warning("Moderate demo health score — inspect readings")
            else:
                st.error("Low demo health score — investigate readings")


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

            st.subheader("Sensor Overview")
            chart_data = pd.DataFrame({
                "Parameter": ["Temperature", "Vibration", "Turbidity", "Gas"],
                "Value": [temperature, vibration, turbidity, gas]
            }).set_index("Parameter")

            st.bar_chart(chart_data)
            st.subheader("📈 Live Sensor History")

            history_df = pd.DataFrame(st.session_state.history)

            if not history_df.empty:
                history_df = history_df.set_index("Time")
                st.line_chart(
                    history_df[["Temperature", "Vibration", "Turbidity", "Gas"]]
                )
            else:
                st.info("Collecting sensor history...")

            st.caption(
                "Demo thresholds only. Calibrate sensors and establish "
                "engineering limits before real transformer use."
            )
        else:
            st.info("Waiting for the first sensor readings...")
    except (json.JSONDecodeError, ValueError, OSError) as error:
        st.error(f"Could not read sensor data: {error}")
else:
    st.warning(
        "Sensor data file not found. Start mqtt_to_dashboard.py "
        "and make sure Wokwi is sending readings."
    )