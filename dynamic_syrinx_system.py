import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from scipy.integrate import solve_ivp

# 1. Параметры аудио-движка
SAMPLE_RATE = 22050  
DURATION = 0.8        # Увеличили длительность, чтобы заметить динамику изгиба
T_SPAN = (0, DURATION)
T_EVAL = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION))

# 2. Нелинейная система сиринкса с динамическим фильтром трахеи (по Илюхину)
def dynamic_syrinx_system(t, y, k_left, k_right, pressure, coupling, max_bend_angle, bend_freq):
    x1, dx1, x2, dx2 = y
    
    # --- МОДУЛЬ ГЕОМЕТРИИ ИЛЮХИНА ---
    # Угол изгиба шеи динамически меняется во времени по синусоидальному закону
    # Птица качает головой с частотой bend_freq (Гц) вокруг максимального угла
    current_bend_angle = max_bend_angle * (0.5 + 0.5 * np.sin(2 * np.pi * bend_freq * t))
    
    # Коэффициент затухания высоких частот зависит от текущего изгиба оси трахеи
    alpha_t = np.clip(current_bend_angle / 120.0, 0.0, 0.92)
    
    # --- АКУСТИКА СИРИНКСА ---
    # Нелинейное затухание в тканях мембран
    gamma1 = 1500 * (x1**2 - 0.01)
    gamma2 = 1500 * (x2**2 - 0.01)
    
    # Взаимное влияние половин сиринкса через общий воздушный столб
    common_feedback = coupling * (dx1 + dx2)
    
    # Уравнения автоколебаний. Изгиб шеи (alpha_t) создает обратное сопротивление,
    # немного гасящее эффективное давление легких
    effective_pressure = pressure * (1.0 - 0.2 * alpha_t)
    
    ddx1 = -gamma1*dx1 - (k_left**2)*x1 + effective_pressure - common_feedback
    ddx2 = -gamma2*dx2 - (k_right**2)*x2 + effective_pressure - common_feedback
    
    return [dx1, ddx1, dx2, ddx2]

# 3. Динамический фильтр бегущей волны в деформируемой трубе
def apply_dynamic_neck_filter(signal, t_eval, max_bend_angle, bend_freq):
    """
    Применяет фильтрацию, параметры которой меняются на каждом шаге времени t
    в соответствии с изменением кривизны шеи.
    """
    filtered_signal = np.zeros_like(signal)
    
    # Начальное состояние фильтра
    y_prev = 0.0
    
    for i, t in enumerate(t_eval):
        # Текущая геометрия изгиба
        current_bend_angle = max_bend_angle * (0.5 + 0.5 * np.sin(2 * np.pi * bend_freq * t))
        alpha_t = np.clip(current_bend_angle / 120.0, 0.0, 0.95)
        
        # Динамическое разностное уравнение фильтра (каждый шаг времени - новые свойства трубы)
        filtered_signal[i] = (1.0 - alpha_t) * signal[i] + alpha_t * y_prev
        y_prev = filtered_signal[i]
        
    return filtered_signal

# 4. Начальные условия
y0 = [0.01, 0.0, 0.01, 0.0]

# 5. Создание интерактивного интерфейса
fig, (ax_wave, ax_spec) = plt.subplots(2, 1, figsize=(10, 8))
plt.subplots_adjust(bottom=0.42, hspace=0.4)

# Исходные параметры
init_k_left = 3200
init_k_right = 3500
init_p = 700
init_c = 250
init_max_bend = 60    # Максимальный изгиб шеи
init_bend_freq = 4    # Частота кивков головой (4 раза в секунду)

# Первая симуляция
sol = solve_ivp(dynamic_syrinx_system, T_SPAN, y0, 
                args=(init_k_left, init_k_right, init_p, init_c, init_max_bend, init_bend_freq), 
                t_eval=T_EVAL, method='RK45')
raw_signal = sol.y[0] + sol.y[2]
audio_signal = apply_dynamic_neck_filter(raw_signal, T_EVAL, init_max_bend, init_bend_freq)

# Отрисовка
line, = ax_wave.plot(T_EVAL, audio_signal, color='darkmagenta', lw=1)
ax_wave.set_title("Динамическая звуковая волна с учетом движений шеи")
ax_wave.set_ylim(-1.5, 1.5)
ax_wave.grid(True)

Pxx, freqs, bins, im = ax_spec.specgram(audio_signal, NFFT=256, Fs=SAMPLE_RATE, noverlap=180, cmap='magma')
ax_spec.set_title("Спектрограмма: Живое изменение обертонов при изгибе шеи (\'эффект вау\')")
ax_spec.set_ylabel("Частота (Гц)")
ax_spec.set_ylim(0, 4000)

# Размещение ползунков (Слайдеров)
ax_kl        = plt.axes([0.3, 0.32, 0.55, 0.025])
ax_kr        = plt.axes([0.3, 0.28, 0.55, 0.025])
ax_p         = plt.axes([0.3, 0.24, 0.55, 0.025])
ax_c         = plt.axes([0.3, 0.20, 0.55, 0.025])
ax_max_bend  = plt.axes([0.3, 0.16, 0.55, 0.025]) # Макс угол
ax_bend_freq = plt.axes([0.3, 0.12, 0.55, 0.025]) # Скорость кивков

s_kl        = Slider(ax_kl, 'Натяжение Левой (Частота 1)', 1000.0, 8000.0, valinit=init_k_left, valfmt='%0.0f')
s_kr        = Slider(ax_kr, 'Натяжение Правой (Частота 2)', 1000.0, 8000.0, valinit=init_k_right, valfmt='%0.0f')
s_p         = Slider(ax_p, 'Давление легких (Сила)', 50.0, 2000.0, valinit=init_p, valfmt='%0.0f')
s_c         = Slider(ax_c, 'Связь (Хаос трахеи)', 0.0, 1000.0, valinit=init_c, valfmt='%0.0f')
s_max_bend  = Slider(ax_max_bend, 'Макс. Изгиб Шеи', 0.0, 90.0, valinit=init_max_bend, valfmt='%0.0f°')
s_bend_freq = Slider(ax_bend_freq, 'Скорость кивков (Гц)', 1.0, 15.0, valinit=init_bend_freq, valfmt='%0.1f Гц')

# 6. Функция динамического обновления
def update(val):
    sol = solve_ivp(dynamic_syrinx_system, T_SPAN, y0, 
                    args=(s_kl.val, s_kr.val, s_p.val, s_c.val, s_max_bend.val, s_bend_freq.val), 
                    t_eval=T_EVAL, method='RK45')
    signal = sol.y[0] + sol.y[2]
    
    # Применяем фильтр динамической геометрии
    signal = apply_dynamic_neck_filter(signal, T_EVAL, s_max_bend.val, s_bend_freq.val)
    
    if np.max(np.abs(signal)) > 0:
        signal = signal / np.max(np.abs(signal))
        
    line.set_ydata(signal)
    ax_spec.clear()
    ax_spec.specgram(signal, NFFT=256, Fs=SAMPLE_RATE, noverlap=180, cmap='magma')
    ax_spec.set_title("Спектрограмма: Живое изменение обертонов при изгибе шеи (\'эффект вау\')")
    ax_spec.set_ylim(0, 4000)
    fig.canvas.draw_idle()

s_kl.on_changed(update)
s_kr.on_changed(update)
s_p.on_changed(update)
s_c.on_changed(update)
s_max_bend.on_changed(update)
s_bend_freq.on_changed(update)

ax_btn = plt.axes([0.45, 0.02, 0.1, 0.04])
btn = Button(ax_btn, 'ПЕТЬ!')
btn.on_clicked(update)

plt.show()
