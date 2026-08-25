import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import math

# 1. تنظیمات اولیه صفحه
st.set_page_config(page_title="Water & Wastewater Hydraulic Simulator", layout="wide")

st.title("🌊 Water & Wastewater Hydraulic Engine (US/Canada Standards)")
st.markdown("---")

# 2. پنل ورودی داده‌ها (Sidebar)
st.sidebar.header("📌 Input Design Parameters")

unit_system = st.sidebar.selectbox("Unit System", ["SI (Metric)", "US Customary"])
fluid_temp = st.sidebar.slider("Fluid Temperature (°C)", 5, 40, 20)

st.sidebar.subheader("Pipeline Geometry")
flow_rate_lps = st.sidebar.number_input("Flow Rate (L/s)", value=100.0, step=5.0)
pipe_diameter_mm = st.sidebar.number_input("Internal Diameter (mm)", value=250.0, step=10.0)
pipe_length_m = st.sidebar.number_input("Pipe Length (m)", value=500.0, step=10.0)
pipe_ks_mm = st.sidebar.number_input("Roughness ks (mm)", value=0.005, format="%.4f")

st.sidebar.subheader("Pumping & Elevation")
static_head = st.sidebar.number_input("Static Head (m)", value=20.0)
elevation_sea = st.sidebar.number_input("Site Elevation (m above sea)", value=100.0)

# 3. محاسبات هیدرولیکی
Q = flow_rate_lps / 1000.0  # m^3/s
D = pipe_diameter_mm / 1000.0  # m
Area = (math.pi * (D ** 2)) / 4.0
Velocity = Q / Area  # m/s

nu = 1.004e-6
Re = (Velocity * D) / nu

# Colebrook-White Friction Factor
f_guess = 0.25 / (math.log10((pipe_ks_mm / (3.7 * pipe_diameter_mm)) + (5.74 / (Re ** 0.9))) ** 2)
f = f_guess
for _ in range(20):
    diff = (1.0 / math.sqrt(f)) - (-2.0 * math.log10((pipe_ks_mm / (3.7 * pipe_diameter_mm)) + (2.51 / (Re * math.sqrt(f)))))
    if abs(diff) < 1e-6:
        break
    df = -0.5 * (f ** -1.5) - (2.0 / math.log(10)) * (1.0 / ((pipe_ks_mm / (3.7 * pipe_diameter_mm)) + (2.51 / (Re * math.sqrt(f))))) * (2.51 / Re) * (-0.5 * (f ** -1.5))
    f = f - diff / df

g = 9.81
hf = f * (pipe_length_m / D) * ((Velocity ** 2) / (2 * g))
tdh = static_head + hf

# 4. نمایش جداول و داده‌ها (Data Tables)
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📊 Calculation Summary Table")
    df_results = pd.DataFrame({
        "Parameter": ["Flow Rate", "Velocity", "Reynolds Number", "Friction Factor (f)", "Head Loss (hf)", "Total Dynamic Head"],
        "Value": [f"{flow_rate_lps:.2f} L/s", f"{Velocity:.2f} m/s", f"{Re:.1e}", f"{f:.4f}", f"{hf:.2f} m", f"{tdh:.2f} m"],
        "Standard Status": [
            "OK",
            "OK (Ten States compliant)" if 0.61 <= Velocity <= 2.4 else "WARNING (Velocity out of bound)",
            "Turbulent" if Re > 4000 else "Laminar",
            "OK",
            "Calculated",
            "Required"
        ]
    })
    st.dataframe(df_results, use_container_width=True)

# 5. نمودار ۲بعدی خط انرژی (2D Plot)
with col2:
    st.subheader("📈 Energy & Hydraulic Grade Line (EGL/HGL)")
    x_pos = np.linspace(0, pipe_length_m, 50)
    egl = tdh - (hf * (x_pos / pipe_length_m))
    hgl = egl - ((Velocity ** 2) / (2 * g))
    
    fig2d = go.Figure()
    fig2d.add_trace(go.Scatter(x=x_pos, y=egl, mode='lines', name='Energy Grade Line (EGL)', line=dict(color='red', width=3)))
    fig2d.add_trace(go.Scatter(x=x_pos, y=hgl, mode='lines', name='Hydraulic Grade Line (HGL)', line=dict(color='blue', dash='dash')))
    fig2d.update_layout(xaxis_title="Pipe Distance (m)", yaxis_title="Elevation / Head (m)", height=350)
    st.plotly_chart(fig2d, use_container_width=True)

# 6. شبیه‌سازی ۳بعدی تعاملی لوله و پروفایل جریان (3D Simulation)
st.subheader("🧊 Interactive 3D Pipeline & Velocity Profile Simulation")

z_3d = np.linspace(0, pipe_length_m, 30)
theta_3d = np.linspace(0, 2 * np.pi, 30)
theta_grid, z_grid = np.meshgrid(theta_3d, z_3d)

r_outer = D / 2.0
x_grid = r_outer * np.cos(theta_grid)
y_grid = r_outer * np.sin(theta_grid)

fig3d = go.Figure()
fig3d.add_trace(go.Surface(x=x_grid, y=y_grid, z=z_grid, colorscale='Blues', opacity=0.4, showscale=False, name="Pipe Wall"))

num_particles = 60
np.random.seed(42)
part_r = np.random.uniform(0, r_outer * 0.85, num_particles)
part_theta = np.random.uniform(0, 2 * np.pi, num_particles)
part_z = np.random.uniform(0, pipe_length_m, num_particles)

part_x = part_r * np.cos(part_theta)
part_y = part_r * np.sin(part_theta)
part_v = Velocity * (1 - (part_r / r_outer)**2)

fig3d.add_trace(go.Scatter3d(
    x=part_x, y=part_y, z=part_z,
    mode='markers',
    marker=dict(size=4, color=part_v, colorscale='Jet', colorbar=dict(title="Velocity (m/s)"), showscale=True),
    name="Fluid Velocity Particles"
))

fig3d.update_layout(
    scene=dict(
        xaxis_title="X (m)", yaxis_title="Y (m)", zaxis_title="Length (m)",
        aspectratio=dict(x=1, y=1, z=3)
    ),
    height=550
)

st.plotly_chart(fig3d, use_container_width=True)
