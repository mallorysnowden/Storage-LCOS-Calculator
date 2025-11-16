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
if not os.path.exists(PLOT_FOLDER):
    os.makedirs(PLOT_FOLDER)

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
        Powercost = st.number_input("Power Cost ($/kWh)", value=0.2, min_value=0.01, step=0.05, format="%.2f")  # Fixed: Use "%.2f" for 2 decimals
        interest_rate = st.number_input("Interest Rate", value=0.08, min_value=0.01, step=0.01, format="%.2f")  # Fixed: Use "%.2f" for 2 decimals
        selected_Tamb_str = st.text_input("Ambient Temps (comma-separated, e.g., -40,-10,0,20)", value="-40,-10
