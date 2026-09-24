import pulp
import pytest

def test_stacking_optimization_feasibility():
    """تست اجرای موفقیت‌آمیز مدل انباشت درآمد و وضعیت بهینه"""
    # ایجاد یک مدل ساده شده برای تست
    model = pulp.LpProblem("Test_Revenue_Stacking", pulp.LpMaximize)
    
    # متغیرهای تست
    p_dis_da = pulp.LpVariable("P_dis_DA", lowBound=0, upBound=1.0)
    r_up_afrr = pulp.LpVariable("R_up_aFRR", lowBound=0, upBound=1.0)
    
    # قید محدودیت اینورتر
    model += p_dis_da + r_up_afrr <= 1.0
    
    # تابع هدف فرضی
    model += 50 * p_dis_da + 100 * r_up_afrr
    
    model.solve(pulp.PULP_CBC_CMD(msg=0))
    
    # بررسی‌ها
    assert pulp.LpStatus[model.status] == "Optimal"
    assert p_dis_da.value() + r_up_afrr.value() <= 1.0  # توان نباید از 1 مگاوات بیشتر شود
    assert r_up_afrr.value() == 1.0  # الگوریتم باید بازار گران‌تر را ترجیح دهد
