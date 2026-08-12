import numpy as np
import json
import time
import requests
from scipy.integrate import solve_ivp

SERVER_URL = "http://localhost:8080"
SAMPLE_RATE = 16000
FRAME_DURATION = 0.2
T_SPAN = (0, FRAME_DURATION)
T_EVAL = np.linspace(0, FRAME_DURATION, int(SAMPLE_RATE * FRAME_DURATION))
Y0_INIT = [0.01, 0.0, 0.01, 0.0]

def advanced_syrinx_physics(t, y, k_left, k_right, pressure, coupling, bend_angle, tissue_degradation):
    """
    Модернизированное ядро по Илюхину с учетом деградации (износа) ткани.
    tissue_degradation: от 0.0 (идеально здоровая) до 1.0 (критический рубец/старение).
    """
    x1, dx1, x2, dx2 = y
    
    # Геометрическое затухание в трахее из-за изгиба шеи
    alpha_geometric = np.clip(bend_angle / 120.0, 0.0, 0.95)
    
    # БИОАКУСТИЧЕСКИЙ СОПРОМАТ:
    # Износ ткани увеличивает базовое вязкое сопротивление мембран и вносит асимметрию.
    # Болезнь чаще поражает одну из половин сильнее (моделируем удар по левой мембране).
    base_damping_left = 1200 + (tissue_degradation * 1500)   # Левая мембрана грубеет сильнее
    base_damping_right = 1200 + (tissue_degradation * 400)   # Правая грубеет меньше
    
    gamma1 = base_damping_left * (x1**2 - 0.01)
    gamma2 = base_damping_right * (x2**2 - 0.01)
    
    # Взаимное влияние половин
    common_feedback = coupling * (dx1 + dx2)
    
    # Эффективное давление гасится извилистостью трахеи
    p_eff = pressure * (1.0 - 0.15 * alpha_geometric)
    
    ddx1 = -gamma1*dx1 - (k_left**2)*x1 + p_eff - common_feedback
    ddx2 = -gamma2*dx2 - (k_right**2)*x2 + p_eff - common_feedback
    
    return [dx1, ddx1, dx2, ddx2]

def send_advanced_telemetry(frame_id, k_l, k_r, press, coupl, bend, degradation):
    sol = solve_ivp(advanced_syrinx_physics, T_SPAN, Y0_INIT, 
                    args=(k_l, k_r, press, coupl, bend, degradation), 
                    t_eval=T_EVAL, method='RK45')
    
    x1_signal = sol.y[0]
    x2_signal = sol.y[2]
    combined_signal = x1_signal + x2_signal
    
    # Метрики цифрового двойника
    rms_energy = float(np.sqrt(np.mean(combined_signal**2)))
    chaos_index = float(np.std(np.diff(combined_signal, 2)))
    
    # Вычисляем реальный коэффициент асимметрии работы мембран на основе их амплитуд
    asymmetry_ratio = float(np.max(np.abs(x1_signal)) / (np.max(np.abs(x2_signal)) + 1e-6))
    
    # Формируем расширенный IoT-пакет
    telemetry_packet = {
        "device_metadata": {
            "sensor_id": "EDGE-SYRINX-TWIN-047",
            "timestamp_utc": int(time.time()),
            "frame_sequence": frame_id
        },
        "input_mechanical_state": {
            "tension_left_n": round(k_l, 2),
            "tension_right_n": round(k_r, 2),
            "internal_pressure_pa": round(press, 2),
            "neck_bend_deg": round(bend, 2),
            "tissue_degradation_factor": round(degradation, 2)  # Передаем фактор износа
        },
        "extracted_physical_metrics": {
            "signal_rms_energy": round(rms_energy, 4),
            "bifurcation_chaos_score": round(chaos_index, 4),
            "membrane_asymmetry_factor": round(asymmetry_ratio, 3)
        },
        # Интеллектуальный статус на основе анализа асимметрии Илюхина
        "diagnostic_status": "HEALTHY" if asymmetry_ratio < 1.2 else ("WARNING_TISSUE_WEAR" if asymmetry_ratio < 1.5 else "CRITICAL_PATHOLOGY_HAZARD")
    }
    
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(SERVER_URL, data=json.dumps(telemetry_packet), headers=headers, timeout=2)
        if response.status_code == 200:
            print(f"[IoT] Пакет №{frame_id} (Износ: {degradation}) отправлен.")
    except requests.exceptions.RequestException:
        print(f"[IoT ERROR] Сервер недоступен для пакета №{frame_id}.")

if __name__ == '__main__':
    print("[INFO] Запуск IoT-передатчика с модулем контроля деградации ткани...")
    
    # Симулируем 5 кадров, где птица постепенно заболевает / стареет (износ растет от 0 до 0.8)
    for frame in range(1, 6):
        simulated_degradation = (frame - 1) * 0.2  # 0.0 -> 0.2 -> 0.4 -> 0.6 -> 0.8
        send_advanced_telemetry(
            frame_id=frame,
            k_l=3200, k_r=3200,  # Мышцы натянуты одинаково, но звук ломается из-за болезни!
            press=800, coupl=200,
            bend=20.0,
            degradation=simulated_degradation
        )
        time.sleep(1.0)
