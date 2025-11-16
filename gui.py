import streamlit as st
import requests
import json
import time
from PIL import Image
import numpy as np
import pandas as pd  # For DataFrame
import os

# Your API URL (replace with yours)
API_URL = "https://storage-lcos-calculator-v2.onrender.com/calculate"

# Plot folder (local; for deploy, use public URL or base64)
PLOT_FOLDER = "plots"  # Create this folder if needed
os.makedirs(PLOT_FOLDER, exist_ok=True)  # Fixed: Always safe, no race condition

st.title("Arctic Energy Storage LCOS Calculator")
st.markdown("Enter parameters below to compute LCOS changes and generate plots.")

# Input Form
with st.form("lcos_inputs"):
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("System Parameters")
        Power = st.number_input("Power (MW)", value=100.0, min_value=1.0, step=10.0)
        DD = st.number_input("Discharge Duration (hours)", value=1.0, min_value=0.1, step=0.5)
        charges_per_year = st.number_input("Charges per Year", value=372.76, min_value=1.0, step=50.0)
        project_lifespan = st.number_input("Project Lifespan (years)", value=50, min_value=1, step=10)
    with col2:
        st.subheader("Economic Parameters")
        Powercost = st.number_input("Power Cost ($/kWh)", value=0.2, min_value=0.01, step=0.05, format="%.2f")
        interest_rate = st.number_input("Interest Rate", value=0.08, min_value=0.01, step=0.01, format="%.2f")
        selected_Tamb_str = st.text_input("Ambient Temps (comma-separated, e.g., -40,-10,0,20)", value="-40,-10,0,20")
        try:
            selected_Tamb = [float(t.strip()) for t in selected_Tamb_str.split(",")]
        except ValueError:
            st.error("Invalid temps—use numbers separated by commas.")
            selected_Tamb = [-40, -10, 0, 20]  # Default fallback

    # Submit button inside form
    submit = st.form_submit_button("Compute LCOS")

if submit:
    # Prepare payload
    inputs = {
        "Power": Power,
        "DD": DD,
        "charges_per_year": charges_per_year,
        "selected_Tamb": selected_Tamb,
        "Powercost": Powercost,
        "interest_rate": interest_rate,
        "project_lifespan": project_lifespan
    }
    
    with st.spinner("Computing... (may take 1-2 min)"):
        start_time = time.time()
        try:
            response = requests.post(API_URL, json=inputs, timeout=300)  # 5 min timeout
            end_time = time.time()
            
            st.subheader(f"Response Status: {response.status_code} ({end_time - start_time:.1f}s)")
            
            if response.status_code == 200:
                data = response.json()
                st.success("Success!")
                
                # Display Timings
                st.subheader("Timings")
                timings_df = pd.DataFrame(list(data['timings'].items()), columns=['Phase', 'Time (s)'])
                st.dataframe(timings_df)
                
                # Display Summary Table (from console log or results)
                st.subheader("LCOS Summary")
                # Extract from log or results (adapt as needed)
                log_preview = data['console_log'][-1000:]  # Last 1000 chars for summary
                st.text_area("Console Log Preview (includes averages/ranges)", log_preview, height=200)
                
                # Display Plot Files
                st.subheader("Generated Plots")
                plot_files = data['plot_files']
                if plot_files:
                    for name, path in plot_files.items():
                        # For local: if path in os.listdir(PLOT_FOLDER): st.image(Image.open(os.path.join(PLOT_FOLDER, path)))
                        st.write(f"**{name}**: [Download PNG](https://your-render-url.com/{path})")  # Update with public path if served
                else:
                    st.info("No plots generated—check logs.")
                
                # Download Results JSON
                st.download_button("Download Full Results JSON", json.dumps(data, indent=2), file_name="lcos_results.json")
                
            else:
                st.error(f"API Error {response.status_code}")
                st.code(response.text, language="json")  # Shows full error body
                
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {e}")
            st.code(str(e), language="text")

# Sidebar for Help
with st.sidebar:
    st.header("Key Variables")
    st.markdown("""
    - **Power (MW)**: System size (scales CAPEX).
    - **DD (hours)**: Storage duration.
    - **Charges/Year**: Cycles (affects degradation).
    - **Powercost ($/kWh)**: Charging cost.
    - **Interest Rate**: Discount for NPV.
    - **Lifespan (years)**: Project duration.
    - **Temps**: List for Arctic/mild comparison.
    """)
    st.info("Plots saved server-side; full grids in JSON download.")
