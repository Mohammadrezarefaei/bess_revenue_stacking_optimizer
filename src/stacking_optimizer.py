import pulp
import numpy as np
import pandas as pd

def run_bess_optimization(degradation_cost_per_mwh=15.0, afrr_activation_rate=0.15):
    """
    اجرای مدل بهینه‌سازی MILP برای انباشت درآمد BESS (Day-Ahead و aFRR)
    """
    # تنظیمات اولیه زمان
    n_hours = 24
    hours = range(n_hours)

    # پروفایل قیمت‌های بازار آلمان (€/MWh و €/MW/h)
    da_prices = np.array([
        45, 40, 38, 36, 40, 55,  # 00:00 - 05:00
        75, 95, 90, 70, 45, 20,  # 06:00 - 11:00
        15, 25, 60, 85, 110, 120,# 12:00 - 17:00
        115, 95, 75, 60, 50, 48  # 18:00 - 23:00
    ])

    afrr_capacity_prices = np.array([
        12, 10, 10, 10, 12, 18,
        25, 30, 28, 22, 15, 12,
        10, 12, 20, 26, 35, 40,
        38, 30, 22, 18, 15, 13
    ])

    # مشخصات سیستم ذخیره‌ساز (باتری ۴ ساعته)
    capacity_mwh = 4.0
    max_power_mw = 1.0
    eta_ch = 0.95
    eta_dis = 0.95

    soc_min = 0.1 * capacity_mwh
    soc_max = 0.9 * capacity_mwh
    initial_soc = 0.5 * capacity_mwh

    # تعریف مدل بهینه‌سازی MILP
    model = pulp.LpProblem("Revenue_Stacking_Degradation", pulp.LpMaximize)

    # متغیرهای تصمیم‌گیری
    p_ch_da = pulp.LpVariable.dicts("P_ch_DA", hours, lowBound=0, upBound=max_power_mw)
    p_dis_da = pulp.LpVariable.dicts("P_dis_DA", hours, lowBound=0, upBound=max_power_mw)
    r_up_afrr = pulp.LpVariable.dicts("R_up_aFRR", hours, lowBound=0, upBound=max_power_mw)
    r_down_afrr = pulp.LpVariable.dicts("R_down_aFRR", hours, lowBound=0, upBound=max_power_mw)
    soc = pulp.LpVariable.dicts("SoC", hours, lowBound=soc_min, upBound=soc_max)

    # توابع مالی
    revenue_da = pulp.lpSum(da_prices[t] * (p_dis_da[t] - p_ch_da[t]) for t in hours)
    revenue_afrr = pulp.lpSum(afrr_capacity_prices[t] * (r_up_afrr[t] + r_down_afrr[t]) for t in hours)

    throughput = pulp.lpSum(
        p_ch_da[t] + p_dis_da[t] + afrr_activation_rate * (r_up_afrr[t] + r_down_afrr[t]) 
        for t in hours
    )
    degradation_cost = degradation_cost_per_mwh * throughput

    # تابع هدف
    model += (revenue_da + revenue_afrr) - degradation_cost

    # قیود فیزیکی و سیستمی
    for t in hours:
        model += p_dis_da[t] + r_up_afrr[t] <= max_power_mw
        model += p_ch_da[t] + r_down_afrr[t] <= max_power_mw
        
        net_power = (eta_ch * (p_ch_da[t] + afrr_activation_rate * r_down_afrr[t])) - \
                    ((p_dis_da[t] + afrr_activation_rate * r_up_afrr[t]) / eta_dis)
                    
        if t == 0:
            model += soc[t] == initial_soc + net_power * 1.0
        else:
            model += soc[t] == soc[t-1] + net_power * 1.0
            
        model += soc[t] - (r_up_afrr[t] / eta_dis) * 1.0 >= soc_min
        model += soc[t] + (eta_ch * r_down_afrr[t]) * 1.0 <= soc_max

    # حل مدل
    model.solve(pulp.PULP_CBC_CMD(msg=0))

    results = {
        "status": pulp.LpStatus[model.status],
        "da_revenue": revenue_da.value(),
        "afrr_revenue": revenue_afrr.value(),
        "total_gross": revenue_da.value() + revenue_afrr.value(),
        "degradation_cost": degradation_cost.value(),
        "net_profit": model.objective.value(),
        "p_ch_da": [p_ch_da[t].value() for t in hours],
        "p_dis_da": [p_dis_da[t].value() for t in hours],
        "r_up_afrr": [r_up_afrr[t].value() for t in hours],
        "r_down_afrr": [r_down_afrr[t].value() for t in hours],
        "soc": [soc[t].value() for t in hours],
        "da_prices": da_prices,
        "afrr_prices": afrr_capacity_prices
    }
    return results
