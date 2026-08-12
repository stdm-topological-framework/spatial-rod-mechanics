import numpy as np
import json
import time
from scipy.integrate import solve_ivp

# --- НАСТРОЙКИ СИСТЕМЫ ---
SAMPLE_RATE = 16000  # Оптимальная частота для Edge-устройств
FRAME_DURATION = 0.2 # Анализ кадрами по 200 миллисекунд
T_SPAN = (0, FRAME_DURATION)
T_EVAL = np.linspace(0, FRAME_DURATION, int(SAMPLE_RATE * FRAME_DURATION))
Y0_INIT = [0.01, 0.0, 0.01, 0.0]

def core_syrinx_physics(t, y, k_left, k_right, pressure, coupling, bend_angle):
    """
    Математическое ядро нелинейных автоколебаний мембран (модель Илюхина).
    k_left, k_right - жесткость (концевое натяжение мышц).
    bend_angle - пространственный изгиб оси резонатора (шеи).
    """
    x1, dx1, x2, dx2 = y
    
    # Геометрический коэффициент затухания обертонов из-за изгиба оси
    alpha_geometric = np.clip(bend_angle / 120.0, 0.0, 0.95)
    
    # Нелинейное упругое сопротивление тканей при экстремальных деформациях
    gamma1 = 1200 * (x1**2 - 0.01)
    gamma2 = 1200 * (x2**2 - 0.01)
    
    # Акустическая обратная связь половин через зазор общего канала
    common_feedback = coupling * (dx1 + dx2)
    
    # Эффективное давление с учетом гидродинамического сопротивления изгиба
    p_eff = pressure * (1.0 - 0.15 * alpha_geometric)
    
    ddx1 = -gamma1*dx1 - (k_left**2)*x1 + p_eff - common_feedback
    ddx2 = -gamma2*dx2 - (k_right**2)*x2 + p_eff - common_feedback
    
    return [dx1, ddx1, dx2, ddx2]

def generate_iot_telemetry(frame_id, k_l, k_r, press, coupl, bend):
    """
    Модуль Edge AI: решает уравнения механики и генерирует сухие IoT-данные.
    Вместо передачи 3200 аудио-отсчетов, функция генерирует 1 компактный JSON.
    """
    # 1. Запуск нелинейного решателя для текущего кадра времени
    sol = solve_ivp(core_syrinx_physics, T_SPAN, Y0_INIT, 
                    args=(k_l, k_r, press, coupl, bend), 
                    t_eval=T_EVAL, method='RK45')
    
    x1_signal = sol.y[0]
    x2_signal = sol.y[2]
    combined_signal = x1_signal + x2_signal
    
    # 2. МЕТРИКИ ЦИФРОВОГО ДВОЙНИКА (Extracting Physical Features)
    # Среднеквадратичная амплитуда (Громкость/Мощность)
    rms_energy = float(np.sqrt(np.mean(combined_signal**2)))
    
    # Индекс хаоса/энтропии (Бифуркационный показатель связи мембран)
    # Считаем через стандартное отклонение ускорения системы
    chaos_index = float(np.std(np.diff(combined_signal, 2)))
    
    # Доминирующие частоты левого и правого стержня по Илюхину
    freq_l = float((k_l / (2 * np.pi)))
    freq_r = float((k_r / (2 * np.pi)))
    
    # Сдвиг частоты из-за пространственного изгиба оси шеи
    # (Эффект Доплера внутри деформируемой геометрии)
    geometric_shift_hz = float(-3.5 * bend) 
    
    # Коэффициент асимметрии износа (разность работы половин)
    asymmetry_ratio = float(np.max(np.abs(x1_signal)) / (np.max(np.abs(x2_signal)) + 1e-6))
    
    # 3. СБОРКА ИНТЕРНЕТ-ПАКЕТА (IoT JSON Payload)
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
            "neck_bend_deg": round(bend, 2)
        },
        "extracted_physical_metrics": {
            "signal_rms_energy": round(rms_energy, 4),
            "bifurcation_chaos_score": round(chaos_index, 4),
            "dominant_freq_left_hz": round(freq_l, 1),
            "dominant_freq_right_hz": round(freq_r, 1),
            "resonance_shift_hz": round(geometric_shift_hz, 1),
            "membrane_asymmetry_factor": round(asymmetry_ratio, 3)
        },
        "diagnostic_status": "CRITICAL_HAZARD_ASYMMETRY" if asymmetry_ratio > 1.5 else "HEALTHY"
    }
    
    return json.dumps(telemetry_packet, indent=4, ensure_ascii=False)

# --- ИМИТАЦИЯ РАБОТЫ IoT-ДАТЧИКА В РЕАЛЬНОМ ВРЕМЕНИ ---
print("[INFO] Запуск IoT-генератора Цифрового Двойника Сиринкса...")
print("[INFO] Имитация изменения геометрии птицы во времени (Брачный танец).\n")

# Птица поет и плавно меняет изгиб шеи и натяжение мышц на протяжении 5 кадров
for frame in range(1, 6):
    # Динамически меняем параметры на каждом шаге, как в живой природе
    simulated_bend = 15.0 * frame       # Шея сгибается сильнее с каждым кадром
    simulated_tension_l = 3000 + (frame * 200)
    simulated_tension_r = 3100 + (frame * 150)
    simulated_pressure = 800 - (frame * 30) # Падает давление выдоха
    
    # Генерация пакета данных на основе дифференциальных уравнений
    json_data = generate_iot_telemetry(
        frame_id=frame,
        k_l=simulated_tension_l,
        k_r=simulated_tension_r,
        press=simulated_pressure,
        coupl=250.0,
        bend=simulated_bend
    )
    
    print(f"--- [ОТПРАВКА IoT ПАКЕТА №{frame}] ---")
    print(json_data)
    print("-" * 40)
    
    # Задержка между отправками данных на сервер
    time.sleep(1.0)
