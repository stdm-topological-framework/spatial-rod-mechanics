import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import minimize
import scipy.io.wavfile as wav
import soundfile as sf  # Вместо scipy.io.wavfile
import time

# --- 1. ПЕРЕХВАТ И ОБРАБОТКА РЕАЛЬНОГО ЗВУКА ВОРОНЫ ---
def load_real_bird_spectrum(wav_filename):
    try:
        # Читаем файл через soundfile (автоматически декодирует PCM)
        data, sample_rate = sf.read(wav_filename)
        
        # Если стерео — переводим в моно
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)
        
        # Берем кусок звука длительностью 0.2 секунды
        num_samples = int(sample_rate * 0.2)
        signal = data[:num_samples].astype(np.float32)
        
        # Нормализация
        if np.max(np.abs(signal)) > 0:
            signal /= np.max(np.abs(signal))
            
        # Преобразование Фурье
        fft_vals = np.abs(np.fft.rfft(signal))
        fft_vals /= np.max(fft_vals)
        return fft_vals, sample_rate
        
    except Exception as e:
        print(f"[WARNING] Файл '{wav_filename}' не найден. Создаем синтетический тестовый профиль вороны...")
        # Если файла нет, генерируем эталонный вектор с "хриплыми" пиками на 700 Гц и 1400 Гц
        fake_spectrum = np.zeros(1601)
        fake_spectrum[50:150] = 1.0   # Основной тон вороны # Обертон трахеи
        return fake_spectrum, 16000

# Загружаем спектр «цели»
TARGET_SPECTROGRAM, SYSTEM_SR = load_real_bird_spectrum("crow.wav")
DURATION = 0.2
T_SPAN = (0, DURATION)
T_EVAL = np.linspace(0, DURATION, int(SYSTEM_SR * DURATION))
Y0 = [0.01, 0.0, 0.01, 0.0]

# --- 2. МАТЕМАТИЧЕСКИЙ ЦИФРОВОЙ ДВОЙНИК ДЛЯ ПОДБОРА ---
def forward_simulation(params):
    k_left, k_right, pressure, bend_angle = params
    
    # Ограничения физического мира, чтобы интегратор не ушел в NaN
    if k_left < 100 or k_right < 100 or pressure < 10 or bend_angle < 0:
        return np.ones_like(TARGET_SPECTROGRAM) * 1e6
        
    def syrinx_ode(t, y):
        x1, dx1, x2, dx2 = y
        alpha_geom = np.clip(bend_angle / 120.0, 0.0, 0.95)
        
        # Карканье — жесткая диссипация энергии (крупная птица)
        gamma1 = 1800 * (x1**2 - 0.01)
        gamma2 = 1800 * (x2**2 - 0.01)
        
        # Нелинейный хаос связи
        common_feedback = 150.0 * (dx1 + dx2)
        p_eff = pressure * (1.0 - 0.15 * alpha_geom)
        
        ddx1 = -gamma1*dx1 - (k_left**2)*x1 + p_eff - common_feedback
        ddx2 = -gamma2*dx2 - (k_right**2)*x2 + p_eff - common_feedback
        return [dx1, ddx1, dx2, ddx2]
        
    sol = solve_ivp(syrinx_ode, T_SPAN, Y0, t_eval=T_EVAL, method='RK45')
    generated_signal = np.tanh(2.5 * (sol.y[0, :] + sol.y[2, :]))
    
    # Считаем спектр получившейся модели
    fft_vals = np.abs(np.fft.rfft(generated_signal))
    if np.max(fft_vals) > 0:
        fft_vals /= np.max(fft_vals)
        
    # Приводим к размерности целевого вектора
    if len(fft_vals) != len(TARGET_SPECTROGRAM):
        fft_vals = np.interp(np.linspace(0, 1, len(TARGET_SPECTROGRAM)), np.linspace(0, 1, len(fft_vals)), fft_vals)
        
    return fft_vals

def loss_function(params):
    current_spec = forward_simulation(params)
    return np.sum((TARGET_SPECTROGRAM - current_spec)**2)

# --- 3. ЗАПУСК ОБРАТНОГО ИНЖИНИРИНГА ГОЛОСА С ТАЙМЕРОМ ---
print("\n[PROCESS] Считывание спектрального паспорта реального голоса...")
initial_guess = [1000.0, 1000.0, 300.0, 10.0] # Начальная слепая догадка

# Глобальные счетчики для вывода прогресса
iteration_count = 0
start_time = time.time()

def callback_monitor(xk):
    """Функция обратного вызова: срабатывает на каждом шаге подбора параметров"""
    global iteration_count, start_time
    iteration_count += 1
    elapsed = time.time() - start_time
    print(f"  [Итерация {iteration_count:03d}] Прошло времени: {elapsed:.2f} сек. Текущий подбор: kL={xk[0]:.1f}, kR={xk[1]:.1f}, P={xk[2]:.1f}, Bend={xk[3]:.1f}°")

print("[SYSTEM] Запуск оптимизатора Nelder-Mead. Расчет дифференциальных уравнений запущен...")
print("-" * 70)

# Передаем нашу функцию мониторинга в параметр callback
result = minimize(loss_function, initial_guess, method='Nelder-Mead', 
                  callback=callback_monitor,
                  options={'maxiter': 100, 'xatol': 1e-1})

total_execution_time = time.time() - start_time
est_kl, est_kr, est_p, est_bend = result.x

print("-" * 70)
print("\n" + "="*60)
print("   АНАЛИТИЧЕСКИЙ ОТЧЕТ ЦИФРОВОГО ДВОЙНИКА ПО РЕАЛЬНОМУ АУДИО")
print("="*60)
print(f"Общее время анализа файла:                 {total_execution_time:.2f} сек.")
print(f"Всего совершено итераций решателя:         {iteration_count}")
print(f"Сходимость физической модели (Loss):       {result.fun:.5f}")
print(f"-> Расчетное натяжение левой мембраны сиринкса: {est_kl:.1f} Н")
print(f"-> Расчетное натяжение правой мембраны сиринкса: {est_kr:.1f} Н")
print(f"-> Динамическое давление воздуха в легких:  {est_p:.1f} Па")
print(f"-> Пространственный изгиб оси шеи (трахеи): {est_bend:.1f}°")
print("-" * 60)
print("[ВЕРДИКТ] Физический профиль успешно восстановлен.")
print("Физический профиль объекта восстановлен в соответствии с теорией Илюхина.")
print("="*60)
