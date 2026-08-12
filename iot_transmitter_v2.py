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

# Теперь у нас 6 переменных состояния: 
# y[0], y[1] - позиция и скорость левой мембраны
# y[2], y[3] - позиция и скорость правой мембраны
# y[4], y[5] - буферные переменные для симуляции запаздывания звуковой волны в трахее (акустический зазор)
Y0_INIT = [0.01, 0.0, 0.01, 0.0, 0.0, 0.0]

def ultimate_syrinx_physics(t, y, k_left, k_right, pressure, coupling, bend_angle, tissue_degradation, wave_delay):
    """
    Максимальное нелинейное ядро Илюхина.
    wave_delay: время задержки обратной волны (паразитная связь дуэта).
    """
    x1, dx1, x2, dx2, delay_buffer1, delay_buffer2 = y
    
    # 1. ГЕОМЕТРИЯ (Проблема 1)
    alpha_geometric = np.clip(bend_angle / 120.0, 0.0, 0.95)
    p_eff = pressure * (1.0 - 0.15 * alpha_geometric)
    
    # 2. СОПРОМАТ И БОЛЕЗНИ (Проблема 2)
    base_damping_left = 1200 + (tissue_degradation * 1500)
    base_damping_right = 1200 + (tissue_degradation * 400)
    gamma1 = base_damping_left * (x1**2 - 0.01)
    gamma2 = base_damping_right * (x2**2 - 0.01)
    
    # 3. ВНУТРЕННИЙ ДУЭТ С ЗАПАЗДЫВАНИЕМ (Проблема 3)
    # Имитируем задержку: скорость изменений половин фильтруется через акустическое расстояние
    # Если wave_delay = 0, связь мгновенная. Если растет - возникает нелинейный хаос.
    tau = max(1e-5, wave_delay)
    ddelay1 = (dx1 - delay_buffer1) / tau
    ddelay2 = (dx2 - delay_buffer2) / tau
    
    # Левая мембрана получает удар от правой с задержкой, и наоборот
    feedback_on_left = coupling * (dx1 + delay_buffer2)
    feedback_on_right = coupling * (dx2 + delay_buffer1)
    
    # Уравнения автоколебаний
    ddx1 = -gamma1*dx1 - (k_left**2)*x1 + p_eff - feedback_on_left
    ddx2 = -gamma2*dx2 - (k_right**2)*x2 + p_eff - feedback_on_right
    
    return [dx1, ddx1, dx2, ddx2, ddelay1, ddelay2]

def send_ultimate_telemetry(frame_id, k_l, k_r, press, coupl, bend, degradation, delay):
    sol = solve_ivp(ultimate_syrinx_physics, T_SPAN, Y0_INIT, 
                    args=(k_l, k_r, press, coupl, bend, degradation, delay), 
                    t_eval=T_EVAL, method='RK45')
    
    x1_signal = sol.y[0]
    x2_signal = sol.y[2]
    combined_signal = x1_signal + x2_signal
    
    # Вычисление физических IoT-метрик
    rms_energy = float(np.sqrt(np.mean(combined_signal**2)))
    
    # Рост хаоса (Bifurcation Score) теперь напрямую зависит от задержки волны!
    chaos_index = float(np.std(np.diff(combined_signal, 2)))
    asymmetry_ratio = float(np.max(np.abs(x1_signal)) / (np.max(np.abs(x2_signal)) + 1e-6))
    
    telemetry_packet = {
        "device_metadata": {
            "sensor_id": "ULTIMATE-SYRINX-TWIN-999",
            "timestamp_utc": int(time.time()),
            "frame_sequence": frame_id
        },
        "input_mechanical_state": {
            "tension_left_n": round(k_l, 2),
            "tension_right_n": round(k_r, 2),
            "internal_pressure_pa": round(press, 2),
            "neck_bend_deg": round(bend, 2),
            "tissue_degradation_factor": round(degradation, 2),
            "acoustic_wave_delay_ms": round(delay * 1000, 3) # Переводим секунды в миллисекунды
        },
        "extracted_physical_metrics": {
            "signal_rms_energy": round(rms_energy, 4),
            "bifurcation_chaos_score": round(chaos_index, 4),
            "membrane_asymmetry_factor": round(asymmetry_ratio, 3)
        },
        "diagnostic_status": "HEALTHY" if (asymmetry_ratio < 1.2 and chaos_index < 500) else 
                             ("CRITICAL_PATHOLOGY_HAZARD" if asymmetry_ratio >= 1.5 else "ACUSTIC_CHAOS_STRESS")
    }
    
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(SERVER_URL, data=json.dumps(telemetry_packet), headers=headers, timeout=2)
        if response.status_code == 200:
            print(f"[IoT] Пакет №{frame_id} отправлен. Хаос (Bifurcation Score): {telemetry_packet['extracted_physical_metrics']['bifurcation_chaos_score']}")
    except requests.exceptions.RequestException:
        print(f"[IoT ERROR] Сервер оффлайн. Пакет №{frame_id} не отправлен.")

if __name__ == '__main__':
    print("[INFO] Запуск финального IoT-передатчика (Все 3 проблемы решены)...")
    
    # Имитируем птицу:
    # Кадр 1: Здоровая, поет спокойно.
    # Кадр 2: Сгибает шею (Проблема 1).
    # Кадр 3: Начинается износ тканей (Проблема 2).
    # Кадр 4-5: Резко растет акустическое запаздывание волны — сиринкс срывается в жесткий хаос (Проблема 3).
    scenarios = [
        {"bend": 0.0,  "degradation": 0.0, "delay": 0.000}, # Норма
        {"bend": 45.0, "degradation": 0.0, "delay": 0.000}, # Изгиб шеи
        {"bend": 45.0, "degradation": 0.5, "delay": 0.000}, # Болезнь ткани
        {"bend": 30.0, "degradation": 0.2, "delay": 0.004}, # Начало хаоса (задержка 4 мс)
        {"bend": 15.0, "degradation": 0.1, "delay": 0.012}, # Жесткий срыв (задержка 12 мс)
    ]
    
    for idx, sc in enumerate(scenarios, 1):
        send_ultimate_telemetry(
            frame_id=idx,
            k_l=3500, k_r=3600,
            press=900, coupl=300,
            bend=sc["bend"],
            degradation=sc["degradation"],
            delay=sc["delay"]
        )
        time.sleep(1.0)
