import numpy as np
import time
import soundfile as sf
from scipy.integrate import solve_ivp
from scipy.optimize import minimize

# --- 1. НАСТРОЙКИ ФАЙЛА И СЕТКИ ---
# Укажите точное имя вашего файла на 3 Мб
WAV_FILENAME = "XC1153023 - Грач - Corvus frugilegus.wav" 
FRAME_DURATION = 0.15  # Шаг анализа — кадры по 150 миллисекунд
Y0 = [0.01, 0.0, 0.01, 0.0]

print(f"[INIT] Загрузка файла: {WAV_FILENAME}...")
try:
    full_data, sample_rate = sf.read(WAV_FILENAME)
    if len(full_data.shape) > 1:
        full_data = np.mean(full_data, axis=1) # Конвертируем в моно
except Exception as e:
    print(f"[ERROR] Не удалось прочитать файл: {e}")
    exit()

# Расчёт временных констант кадра
samples_per_frame = int(sample_rate * FRAME_DURATION)
total_frames = min(5, len(full_data) // samples_per_frame) # Анализируем первые 5 кадров для экономии времени
T_SPAN = (0, FRAME_DURATION)
T_EVAL = np.linspace(0, FRAME_DURATION, samples_per_frame)

# --- 2. МАТЕМАТИЧЕСКАЯ ФИЗИКА (ЯДРО ИЛЮХИНА) ---
def get_spectrum(signal):
    fft_vals = np.abs(np.fft.rfft(signal))
    if np.max(fft_vals) > 0:
        fft_vals /= np.max(fft_vals)
    return fft_vals

def forward_simulation(params, target_len):
    k_left, k_right, pressure, bend_angle = params
    if k_left < 100 or k_right < 100 or pressure < 10 or bend_angle < 0:
        return np.ones(target_len) * 1e6
        
    def syrinx_ode(t, y):
        x1, dx1, x2, dx2 = y
        alpha_geom = np.clip(bend_angle / 120.0, 0.0, 0.95)
        gamma1 = 1800 * (x1**2 - 0.01)
        gamma2 = 1800 * (x2**2 - 0.01)
        common_feedback = 150.0 * (dx1 + dx2)
        p_eff = pressure * (1.0 - 0.15 * alpha_geom)
        
        ddx1 = -gamma1*dx1 - (k_left**2)*x1 + p_eff - common_feedback
        ddx2 = -gamma2*dx2 - (k_right**2)*x2 + p_eff - common_feedback
        return [dx1, ddx1, dx2, ddx2]
        
    sol = solve_ivp(syrinx_ode, T_SPAN, Y0, t_eval=T_EVAL, method='RK45')
    generated_signal = np.tanh(2.5 * (sol.y[0, :] + sol.y[2, :]))
    
    fft_vals = get_spectrum(generated_signal)
    if len(fft_vals) != target_len:
        fft_vals = np.interp(np.linspace(0, 1, target_len), np.linspace(0, 1, len(fft_vals)), fft_vals)
    return fft_vals

# --- 3. ЦИКЛ ДИНАМИЧЕСКОГО АНАЛИЗА ПО КАДРАМ ВРЕМЕНИ ---
print(f"[START] Запуск динамического цифрового двойника. Всего кадров для анализа: {total_frames}")
print("=" * 80)
print(f"{'Время (сек)':<12} | {'Изгиб шеи':<12} | {'Колебания Левой':<18} | {'Колебания Правой':<18} | {'Статус'}")
print("-" * 80)

global_start_time = time.time()

for frame_idx in range(total_frames):
    start_sample = frame_idx * samples_per_frame
    end_sample = start_sample + samples_per_frame
    
    # Вырезаем текущий временной кадр живого голоса грача
    frame_data = full_data[start_sample:end_sample].astype(np.float32)
    if np.max(np.abs(frame_data)) > 0:
        frame_data /= np.max(np.abs(frame_data))
        
    target_spectrum = get_spectrum(frame_data)
    
    # Оптимизатор под конкретный кадр
    def loss_function(params):
        current_spec = forward_simulation(params, len(target_spectrum))
        return np.sum((target_spectrum - current_spec)**2)
    
    # Начальная догадка для кадра
    initial_guess = [1200.0, 1300.0, 400.0, 15.0]
    
    # Быстрый поиск параметров для текущего момента времени
    result = minimize(loss_function, initial_guess, method='Nelder-Mead', options={'maxiter': 40})
    est_kl, est_kr, est_p, est_bend = result.x
    
    # ПЕРЕВЕДЕМ ЖЕСТКОСТЬ В РЕАЛЬНОЕ ЧИСЛО КОЛЕБАНИЙ МЕМБРАНЫ В СЕКУНДУ (Гц)
    # Формула частоты: f = omega / (2 * pi), где omega = k
    frequency_left = est_kl / (2 * np.pi)
    frequency_right = est_kr / (2 * np.pi)
    
    # Текущая временная отметка в аудиофайле
    current_time_sec = frame_idx * FRAME_DURATION
    
    # Выводим строку динамического отчета
    print(f"{current_time_sec:<12.2f} | {est_bend:<10.1f}° | {frequency_left:<13.1f} Гц | {frequency_right:<13.1f} Гц | OK")

total_time = time.time() - global_start_time
print("-" * 80)
print(f"[SUCCESS] Динамический трекинг завершен за {total_time:.2f} сек.")
print("=" * 80)
