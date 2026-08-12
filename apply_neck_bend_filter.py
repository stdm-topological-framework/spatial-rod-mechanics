import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from scipy.integrate import solve_ivp
from scipy.signal import lfilter

# 1. Параметры аудио-движка
SAMPLE_RATE = 22050  
DURATION = 0.5       
T_SPAN = (0, DURATION)
T_EVAL = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION))

# 2. Нелинейная система сиринкса
def syrinx_system(t, y, k_left, k_right, pressure, coupling):
    x1, dx1, x2, dx2 = y
    
    # Нелинейное затухание в тканях
    gamma1 = 1500 * (x1**2 - 0.01)
    gamma2 = 1500 * (x2**2 - 0.01)
    
    # Взаимное влияние половин сиринкса
    common_feedback = coupling * (dx1 + dx2)
    
    # Уравнения автоколебаний
    ddx1 = -gamma1*dx1 - (k_left**2)*x1 + pressure - common_feedback
    ddx2 = -gamma2*dx2 - (k_right**2)*x2 + pressure - common_feedback
    
    return [dx1, ddx1, dx2, ddx2]

# 3. Акустический фильтр изгиба шеи по Илюхину
def apply_neck_bend_filter(signal, bend_angle):
    """
    Моделирует прохождение звука через изогнутую трубу.
    Чем больше угол изгиба (в градусах), тем сильнее гасятся высокие частоты
    и тем сильнее выражен резонанс «сабвуфера».
    """
    # Переводим угол в диапазон от 0 до 1 для коэффициентов
    alpha = np.clip(bend_angle / 120.0, 0.0, 0.95)
    
    # Математика фильтра: динамический спад частот из-за кривизны геометрии
    # Коэффициенты авторегрессионного фильтра (простая физическая модель затухания волны)
    b = [1.0 - alpha]
    a = [1.0, -alpha]
    
    filtered_signal = lfilter(b, a, signal)
    return filtered_signal

# 4. Начальные условия
y0 = [0.01, 0.0, 0.01, 0.0]

# 5. Создание интерфейса
fig, (ax_wave, ax_spec) = plt.subplots(2, 1, figsize=(10, 7))
plt.subplots_adjust(bottom=0.4, hspace=0.4)

# Исходные параметры
init_k_left = 3200
init_k_right = 3400
init_p = 600
init_c = 250
init_bend = 0  # Изначально шея прямая (0 градусов)

# Первичный запуск
sol = solve_ivp(syrinx_system, T_SPAN, y0, args=(init_k_left, init_k_right, init_p, init_c), t_eval=T_EVAL, method='RK45')
raw_signal = sol.y[0] + sol.y[2]
audio_signal = apply_neck_bend_filter(raw_signal, init_bend)

# Отрисовка графиков
line, = ax_wave.plot(T_EVAL[:1000], audio_signal[:1000], color='indigo', lw=1.5)
ax_wave.set_title("Форма звуковой волны с учетом геометрии трахеи")
ax_wave.set_ylim(-1.5, 1.5)
ax_wave.grid(True)

Pxx, freqs, bins, im = ax_spec.specgram(audio_signal, NFFT=256, Fs=SAMPLE_RATE, noverlap=128, cmap='viridis')
ax_spec.set_title("Спектрограмма: влияние изгиба на обертоны")
ax_spec.set_ylabel("Частота (Гц)")
ax_spec.set_ylim(0, 4000)

# Размещение ползунков
ax_kl   = plt.axes([0.25, 0.27, 0.6, 0.03])
ax_kr   = plt.axes([0.25, 0.22, 0.6, 0.03])
ax_p    = plt.axes([0.25, 0.17, 0.6, 0.03])
ax_c    = plt.axes([0.25, 0.12, 0.6, 0.03])
ax_bend = plt.axes([0.25, 0.07, 0.6, 0.03]) # Новый ползунок

s_kl   = Slider(ax_kl, 'Натяжение Левой', 1000.0, 8000.0, valinit=init_k_left, valfmt='%0.0f')
s_kr   = Slider(ax_kr, 'Натяжение Правой', 1000.0, 8000.0, valinit=init_k_right, valfmt='%0.0f')
s_p    = Slider(ax_p, 'Давление легких', 50.0, 2000.0, valinit=init_p, valfmt='%0.0f')
s_c    = Slider(ax_c, 'Связь (Трахея)', 0.0, 1000.0, valinit=init_c, valfmt='%0.0f')
s_bend = Slider(ax_bend, 'Изгиб Шеи (Градусы)', 0.0, 90.0, valinit=init_bend, valfmt='%0.0f°')

# 6. Функция обновления данных
def update(val):
    sol = solve_ivp(syrinx_system, T_SPAN, y0, args=(s_kl.val, s_kr.val, s_p.val, s_c.val), t_eval=T_EVAL, method='RK45')
    signal = sol.y[0] + sol.y[2]
    
    # Применяем фильтр геометрии шеи
    signal = apply_neck_bend_filter(signal, s_bend.val)
    
    if np.max(np.abs(signal)) > 0:
        signal = signal / np.max(np.abs(signal))
        
    line.set_ydata(signal[:1000])
    ax_spec.clear()
    ax_spec.specgram(signal, NFFT=256, Fs=SAMPLE_RATE, noverlap=128, cmap='viridis')
    ax_spec.set_title("Спектрограмма: влияние изгиба на обертоны")
    ax_spec.set_ylim(0, 4000)
    fig.canvas.draw_idle()

s_kl.on_changed(update)
s_kr.on_changed(update)
s_p.on_changed(update)
s_c.on_changed(update)
s_bend.on_changed(update)

ax_btn = plt.axes([0.45, 0.01, 0.1, 0.04])
btn = Button(ax_btn, 'ПЕТЬ!')
btn.on_clicked(update)

plt.show()
