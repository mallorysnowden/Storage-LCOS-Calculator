import streamlit as st
import requests
import json
import time
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib.colors as mcolors
from matplotlib.colors import ListedColormap
from matplotlib.path import Path
from matplotlib.patches import PathPatch
import matplotlib.ticker as ticker
import os

# Your API URL (replace with backend)
API_URL = "https://lcos-gui.onrender.com/calculate"

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
            selected_Tamb = [-40, -10, 0, 20]

    submit = st.form_submit_button("Compute LCOS")

if submit:
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
            response = requests.post(API_URL, json=inputs, timeout=300)
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
                log_preview = data['console_log'][-1000:]
                st.text_area("Console Log Preview (includes averages/ranges)", log_preview, height=200)
                
                # Display Plot Files (List + Recreation)
                st.subheader("Generated Plots")
                plot_files = data['plot_files']
                if plot_files:
                    st.write("Plots recreated below from results data.")
                else:
                    st.info("No plots generated—check logs.")
                
                # Recreate Plots from data['results']
                results = data['results']
                charges_values = results['charges_values']
                DD_values = results['DD_values']
                subprograms = results['subprograms']
                subprogram_colors = results['subprogram_colors']
                min_baseLCOS_indices = np.array(results['min_baseLCOS_indices'])
                min_newLCOS_indices = np.array(results['min_newLCOS_indices'])
                min_LCOSchange = np.array(results['min_LCOSchange'])
                min_baseLCOS = np.array(results['min_baseLCOS'])
                min_newLCOS = np.array(results['min_newLCOS'])
                
                # Plot 1: Side-by-side indices scatter
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
                X, Y = np.meshgrid(charges_values, DD_values)
                X_flat, Y_flat = X.ravel(), Y.ravel()
                colors = ['white'] + [subprogram_colors[prog] for prog in subprograms]
                custom_cmap = ListedColormap(colors)
                scatter1 = ax1.scatter(X_flat, Y_flat, c=min_baseLCOS_indices.ravel(), cmap=custom_cmap, s=50, marker='o', edgecolors='white', linewidth=0.5)
                ax1.set_xscale('log', base=10)
                ax1.set_yscale('log', base=4)
                ax1.set_xlabel('Charges per Year (CPY)')
                ax1.set_title('Min LCOS Storage Technology in Mild Climates')
                ax1.set_ylabel('Discharge Duration (hours)')
                scatter2 = ax2.scatter(X_flat, Y_flat, c=min_newLCOS_indices.ravel(), cmap=custom_cmap, s=50, marker='o', edgecolors='white', linewidth=0.5)
                ax2.set_xscale('log', base=10)
                ax2.set_yscale('log', base=4)
                ax2.set_xlabel('Charges per Year (CPY)')
                ax2.set_title('Min LCOS Storage Technology in Arctic Climates')
                cbar = fig.colorbar(scatter2, ax=[ax1, ax2], location='right')
                cbar.set_ticks(np.arange(len(subprograms)))
                cbar.set_ticklabels([prog.replace('calcs', '') for prog in subprograms])
                fig.subplots_adjust(left=0.05, right=0.75, wspace=0.2)
                st.pyplot(fig)
                plt.close(fig)
                
                # Plot 2: Average LCOS change bar
                avg_LCOSchange = np.zeros(len(subprograms))
                counts = np.zeros(len(subprograms), dtype=int)
                for k in range(len(subprograms)):
                    mask = min_baseLCOS_indices == k
                    valid_LCOSchange = min_LCOSchange[mask]
                    valid_LCOSchange = valid_LCOSchange[~np.isnan(valid_LCOSchange)]
                    counts[k] = len(valid_LCOSchange)
                    avg_LCOSchange[k] = np.mean(valid_LCOSchange) if counts[k] > 0 else np.nan
                color_map = {'BESS': 'red', 'H2': 'green', 'CAES': 'pink', 'PHS': 'blue', 'Flywheel': 'purple'}
                colors = [color_map.get(sp.replace('calcs', ''), 'gray') for sp in subprograms]
                fig, ax = plt.subplots(figsize=(6, 4.5))
                bars = ax.bar(range(len(subprograms)), avg_LCOSchange, color=colors, edgecolor='black')
                ax.set_xticks(range(len(subprograms)))
                ax.set_xticklabels([sp.replace('calcs', '') for sp in subprograms], rotation=45, ha='right')
                ax.set_ylabel('Average LCOS Change (%)')
                ax.set_title(f'Average LCOS Change in the Arctic by Technology \nP = {Power:0.0f}MW, Power @ {Powercost:0.2f} USD/kWh')
                for bar, value in zip(bars, avg_LCOSchange):
                    if not np.isnan(value):
                        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{value:.1f}%", ha='center', va='bottom')
                plt.tight_layout()
                st.pyplot(fig)
                plt.close(fig)
                
                # Add more recreations for other plots (e.g., marker scatter, LCOS change)—expand as needed
                
                # Download Results JSON
                st.download_button("Download Full Results JSON", json.dumps(data, indent=2), file_name="lcos_results.json")
                
            else:
                st.error(f"API Error {response.status_code}")
                st.code(response.text, language="json")
                
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
    st.info("Plots recreated from data; full grids in JSON download.")
