import numpy as np
import json
import time
import requests  # pip install requests
from scipy.integrate import solve_ivp

SERVER_URL = "http://localhost:8080" # Адрес нашего сервера
SAMPLE_RATE = 16000
FRAME_DURATION = 0.2
T_SPAN = (0, FRAME_DURATION)
T_EVAL = np.linspace(0, FRAME_DURATION, int(SAMPLE_RATE * FRAME_DURATION))
Y0_INIT = [0.01, 0.0, 0.01, 0.0]

def core_syrinx_physics(t, y, k_left, k_right, pressure, coupling, bend_angle):
    x1, dx1, x2, dx2 = y
    alpha_geometric = np.clip(bend_angle / 120.0, 0.0, 0.95)
    gamma1 = 1200 * (x1**2 - 0.01)
    gamma2 = 1200 * (x2**2 - 0.01)
    common_feedback = coupling * (dx1 + dx2)
    p_eff = pressure * (1.0 - 0.15 * alpha_geometric)
    ddx1 = -gamma1*dx1 - (k_left**2)*x1 + p_eff - common_feedback
    ddx2 = -gamma2*dx2 - (k_right**2)*x2 + p_eff - common_feedback
    return [dx1, ddx1, dx2, ddx2]

def send_to_server(frame_id, k_l, k_r, press, coupl, bend):
    sol = solve_ivp(core_syrinx_physics, T_SPAN, Y0_INIT, args=(k_l, k_r, press, coupl, bend), t_eval=T_EVAL, method='RK45')
    combined_signal = sol.y + sol.y
    
    # Расчет физических параметров Илюхина
    rms_energy = float(np.sqrt(np.mean(combined_signal**2)))
    chaos_index = float(np.std(np.diff(combined_signal, 2)))
    asymmetry_ratio = float(np.max(np.abs(sol.y)) / (np.max(np.abs(sol.y)) + 1e-6))
    
    # Пакет данных
    telemetry_packet = {
        "device_metadata": {"sensor_id": "EDGE-SYRINX-TWIN-047", "timestamp_utc": int(time.time()), "frame_sequence": frame_id},
        "input_mechanical_state": {"tension_left_n": round(k_l, 2), "tension_right_n": round(k_r, 2), "internal_pressure_pa": round(press, 2), "neck_bend_deg": round(bend, 2)},
        "extracted_physical_metrics": {"signal_rms_energy": round(rms_energy, 4), "bifurcation_chaos_score": round(chaos_index, 4), "membrane_asymmetry_factor": round(asymmetry_ratio, 3)},
        "diagnostic_status": "CRITICAL_HAZARD_ASYMMETRY" if asymmetry_ratio > 1.5 else "HEALTHY"
    }
    
    # СЕТЕВОЙ ПЕРЕДАТЧИК (Отправка JSON по HTTP)
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(SERVER_URL, data=json.dumps(telemetry_packet), headers=headers, timeout=2)
        if response.status_code == 200:
            print(f"[IoT] Пакет №{frame_id} успешно отправлен на сервер.")
    except requests.exceptions.RequestException as e:
        print(f"[IoT ERROR] Не удалось отправить пакет №{frame_id}: Сервер недоступен.")

# Цикл симуляции птицы в движении
if __name__ == '__main__':
    print("[INFO] Запуск датчика. Начинаем стриминг физической телеметрии...")
    for frame in range(1, 6):
        send_to_server(frame_id=frame, k_l=3000 + (frame*100), k_r=3100, press=750, coupl=200, bend=10.0 * frame)
        time.sleep(1.0)
