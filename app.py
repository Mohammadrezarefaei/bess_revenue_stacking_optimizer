import streamlit as st
import matplotlib.pyplot as plt
from src.stacking_optimizer import run_bess_optimization

st.set_page_config(page_title="BESS Revenue Stacking Optimizer", layout="wide")

st.title("⚡ BESS Revenue Stacking & Degradation Optimizer (German Market)")
st.markdown("This dashboard optimizes a **4 MWh / 1 MW** Battery Energy Storage System co-optimizing **Day-Ahead Arbitrage** and **aFRR Frequency Reserves** while accounting for cell degradation costs.")

# نوار تنظیمات کناری (Sidebar)
st.sidebar.header("Configuration Parameters")
deg_cost = st.sidebar.slider("Degradation Cost (€ / MWh Throughput)", min_value=0.0, max_value=50.0, value=15.0, step=1.0)
activation_rate = st.sidebar.slider("aFRR Activation Rate (%)", min_value=5.0, max_value=40.0, value=15.0, step=1.0) / 100.0

# اجرای مدل با پارامترهای جدید
res = run_bess_optimization(degradation_cost_per_mwh=deg_cost, afrr_activation_rate=activation_rate)

# نمایش کارت‌های نتایج مالی (Metrics)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Gross DA Revenue", f"€{res['da_revenue']:.2f}")
col2.metric("Gross aFRR Revenue", f"€{res['afrr_revenue']:.2f}")
col3.metric("Degradation Cost", f"-€{res['degradation_cost']:.2f}")
col4.metric("Net Profit", f"€{res['net_profit']:.2f}", delta="Optimal")

st.divider()

# رسم نمودارها
hours = range(24)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

# نمودار دیسپچ توان
ax1.bar(hours, res['p_dis_da'], label='DA Discharge', color='blue', alpha=0.7)
ax1.bar(hours, res['r_up_afrr'], bottom=res['p_dis_da'], label='aFRR Up Reserve', color='lightblue', edgecolor='black')
ax1.bar(hours, [-x for x in res['p_ch_da']], label='DA Charge', color='red', alpha=0.7)
ax1.bar(hours, [-x for x in res['r_down_afrr']], bottom=[-x for x in res['p_ch_da']], label='aFRR Down Reserve', color='lightcoral', edgecolor='black')
ax1.axhline(1.0, color='black', linestyle='--', linewidth=1.5, label='Inverter Max Power (1MW)')
ax1.axhline(-1.0, color='black', linestyle='--', linewidth=1.5)
ax1.set_ylabel('Power (MW)')
ax1.set_title('BESS Power Dispatch Stack')
ax1.legend(loc='upper right', bbox_to_anchor=(1.15, 1))
ax1.grid(True, linestyle=':', alpha=0.6)

# نمودار وضعیت شارژ (SoC)
ax2.plot(hours, res['soc'], color='purple', marker='o', linewidth=2, label='SoC (MWh)')
ax2.axhline(3.6, color='red', linestyle='--', alpha=0.5, label='Max SoC (90%)')
ax2.axhline(0.4, color='red', linestyle='--', alpha=0.5, label='Min SoC (10%)')
ax2.set_xlabel('Hour of Day')
ax2.set_ylabel('Energy (MWh)')
ax2.set_title('Battery State of Charge (SoC) Dynamics')
ax2.legend(loc='upper right', bbox_to_anchor=(1.15, 1))
ax2.grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()
st.pyplot(fig)
