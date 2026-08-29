"""
Comparison dashboard. Run AFTER you've generated some data with both
standard_iot_client.py and edge_client.py (including at least one
--outage run of each).

Usage:
    streamlit run dashboard.py
"""
import os

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Standard IoT vs Edge Analytics", layout="wide")
st.title("Standard IoT vs Edge Analytics — Attendance System")
st.caption("Problem Statement 20 — comparative implementation")


def load_csv(path):
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()


std_df = load_csv("metrics_standard.csv")
edge_df = load_csv("metrics_edge.csv")
attendance_df = load_csv("attendance.csv")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Average Latency (ms)")
    if not std_df.empty or not edge_df.empty:
        latency_summary = pd.DataFrame({
            "Standard IoT": [std_df[std_df.status == "present"]["latency_ms"].mean()
                              if not std_df.empty else None],
            "Edge Analytics": [edge_df[edge_df.status == "synced"]["latency_ms"].mean()
                                if not edge_df.empty else None],
        }, index=["Avg Latency (ms)"])
        st.bar_chart(latency_summary.T)
    else:
        st.info("Run standard_iot_client.py and edge_client.py first.")

with col2:
    st.subheader("Average Payload Size (bytes)")
    if not std_df.empty or not edge_df.empty:
        bandwidth_summary = pd.DataFrame({
            "Standard IoT (raw image)": [std_df["bytes_sent"].mean() if not std_df.empty else None],
            "Edge Analytics (record only)": [edge_df["bytes_sent"].mean() if not edge_df.empty else None],
        }, index=["Avg Bytes Sent"])
        st.bar_chart(bandwidth_summary.T)

st.subheader("Reliability During Simulated Internet Outage")
outage_col1, outage_col2 = st.columns(2)
with outage_col1:
    st.markdown("**Standard IoT**")
    if not std_df.empty:
        outage_rows = std_df[std_df.outage_simulated == True]
        failed = (outage_rows.status == "failed_no_connection").sum()
        st.metric("Attendance records lost during outage", failed)
    else:
        st.info("No data yet.")

with outage_col2:
    st.markdown("**Edge Analytics**")
    if not edge_df.empty:
        outage_rows = edge_df[edge_df.outage_simulated == True]
        queued = (outage_rows.status == "queued_offline").sum()
        st.metric("Attendance records queued (not lost) during outage", queued)
    else:
        st.info("No data yet.")

st.subheader("Attendance Log")
if not attendance_df.empty:
    st.dataframe(attendance_df, use_container_width=True)
else:
    st.info("No attendance recorded yet.")
