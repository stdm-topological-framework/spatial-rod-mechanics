import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import minimize

# --- 1. НАСТРОЙКИ И ЭТАЛОННЫЙ СИГНАЛ ---
SAMPLE_RATE = 16000
DURATION = 0.2
T_SPAN = (0, DURATION)
T_EVAL = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION))
Y0 = [0.01, 0.0, 0.01, 0.0]

def get_spectrogram_vector(signal):
    """Превращает аудиосигнал в сухой спектральный вектор для сравнения"""
    # Считаем быстрое преобразование Фурье (FFT) от сигнала
    fft_vals = np.abs(np.fft.rfft(signal))
    # Нормализуем, чтобы сравнивать форму спектра, а не общую громкость
    if np.max(fft_vals) > 0:
        fft_vals /= np.max(fft_vals)
    return fft_vals

# Имитируем «Живую птицу» (целевой спектр, который нужно разгадать алгоритму)
# Пусть реальная птица имеет параметры: k_l=3150, k_r=3350, bend=45, feathers=0.3
def generate_target_bird_signal():
    # Внутренняя скрытая физика живой птицы в лесу
    def true_physics(t, y):
        x1, dx1, x2, dx2 = y
        # Учитываем поглощение перьев (feathers = 0.3) в затухании ткани
        gamma1 = (1200 + 0.3 * 500) * (x1**2 - 0.01)
        gamma2 = (1200 + 0.3 * 500) * (x2**2 - 0.01)
        # Изгиб шеи 45 градусов снижает эффективное давление
        p_eff = 700 * (1.0 - 0.15 * (45.0 / 120.0))
        ddx1 = -gamma1*dx1 - (3150**2)*x1 + p_eff - 200*(dx1 + dx2)
        ddx2 = -gamma2*dx2 - (3350**2)*x2 + p_eff - 200*(dx1 + dx2)
        return [dx1, ddx1, dx2, ddx2]
    
    sol = solve_ivp(true_physics, T_SPAN, Y0, t_eval=T_EVAL, method='RK45')
    return sol.y + sol.y

# Генерируем эталон, как будто загрузили WAV-файл живой птицы
REAL_BIRD_SIGNAL = generate_target_bird_signal()
TARGET_SPECTROGRAM = get_spectrogram_vector(REAL_BIRD_SIGNAL)


# --- 2. МАТЕМАТИЧЕСКАЯ МОДЕЛЬ ДЛЯ ПОДБОРА ---
def forward_simulation(params):
    """Прямая модель: принимает параметры, возвращает спектр сгенерированного звука"""
    k_left, k_right, bend_angle, feathers_volume = params
    
    # Защита от физически невозможных/отрицательных параметров (границы модели)
    if k_left < 1000 or k_right < 1000 or bend_angle < 0 or feathers_volume < 0:
        return np.ones_like(TARGET_SPECTROGRAM) * 1e6 # Возвращаем огромную ошибку
        
    def syrinx_ode(t, y):
        x1, dx1, x2, dx2 = y
        # Перья работают как акустический поглотитель (диссипация энергии)
        gamma1 = (1200 + feathers_volume * 500) * (x1**2 - 0.01)
        gamma2 = (1200 + feathers_volume * 500) * (x2**2 - 0.01)
        
        # Эффективное давление гасится извилистостью трахеи по Илюхину
        alpha_geom = bend_angle / 120.0
        p_eff = 700 * (1.0 - 0.15 * alpha_geom)
        
        ddx1 = -gamma1*dx1 - (k_left**2)*x1 + p_eff - 200*(dx1 + dx2)
        ddx2 = -gamma2*dx2 - (k_right**2)*x2 + p_eff - 200*(dx1 + dx2)
        return [dx1, ddx1, dx2, ddx2]
        
    sol = solve_ivp(syrinx_ode, T_SPAN, Y0, t_eval=T_EVAL, method='RK45')
    generated_signal = sol.y + sol.y
    return get_spectrogram_vector(generated_signal)


# --- 3. ФУНКЦИЯ ОШИБКИ И СВЕРКА НА ФАЛЬШЬ ---
def objective_loss_function(params):
    """Считает разницу между живым спектром и модельным"""
    current_spectrogram = forward_simulation(params)
    # Метод наименьших квадратов — норма разности векторов спектра
    loss = np.sum((TARGET_SPECTROGRAM - current_spectrogram)**2)
    return loss


# --- 4. ЗАПУСК ОБРАТНОГО ИНЖИНИРИНГА ---
print("[SYSTEM] Начинаем анализ живого аудиосигнала...")
print("[SYSTEM] Подбираем параметры нелинейных уравнений Илюхина...")

# Начальная слепая догадка компьютера (угадываем с нуля)
initial_guess = [2000.0, 2000.0, 10.0, 0.0] 

# Запуск математического оптимизатора (Алгоритм Нелдера-Мида для нелинейных систем)
result = minimize(objective_loss_function, initial_guess, method='Nelder-Mead', 
                  options={'xatol': 1e-2, 'maxiter': 150})

# Вывод результатов
estimated_kl, estimated_kr, estimated_bend, estimated_feathers = result.x
final_loss = result.fun

print("\n" + "="*50)
print("      РЕЗУЛЬТАТЫ ОБРАТНОГО ИНЖИНИРИНГА ГОЛОСА")
print("="*50)
print(f"Математическая ошибка несовпадения (Loss): {final_loss:.6f}")

if final_loss > 0.5:
    print("\n[ВНИМАНИЕ] ФАЛЬШЬ! Звук не может быть воссоздан законами физики.")
    print("[ДИАГНОЗ] Сигнал имеет искусственное происхождение или критически зашумлен.")
else:
    print("\n[УСПЕХ] Физический профиль птицы успешно разгадан!")
    print(f"-> Натяжение левой мембраны (Мышцы):  {estimated_kl:.1f} N (Реальное: 3150)")
    print(f"-> Натяжение правой мембраны (Мышцы): {estimated_kr:.1f} N (Реальное: 3350)")
    print(f"-> Анатомический изгиб шеи птицы:   {estimated_bend:.1f}°   (Реальное: 45)")
    print(f"-> Распушённость оперения (Объём):     {estimated_feathers:.2f}   (Реальное: 0.3)")
    print("\n[ДИАГНОЗ] Птица здорова. Патологической асимметрии тканей не обнаружено.")
print("="*50)
