import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from scipy.integrate import solve_ivp
import sounddevice as sd  # ОБЯЗАТЕЛЬНО: pip install sounddevice
import threading

# 1. Глобальные аудио-настройки (Повысили качество для устранения 8-битности)
SAMPLE_RATE = 44100  # Студийное качество
CHUNK_DURATION = 0.04  # Меньше задержка (40 мс) для мгновенного отклика ползунков
T_SPAN = (0, CHUNK_DURATION)
T_EVAL = np.linspace(0, CHUNK_DURATION, int(SAMPLE_RATE * CHUNK_DURATION))

current_kl = 2500.0
current_kr = 2700.0
current_p = 600.0
current_c = 50.0
current_max_bend = 45.0
current_bend_freq = 3.0

is_playing = False
y_state = [0.01, 0.0, 0.01, 0.0]  

# 2. Нелинейная система сиринкса
def syrinx_core(t, y, k_left, k_right, pressure, coupling, max_bend_angle, bend_freq, global_time):
    x1, dx1, x2, dx2 = y
    
    t_abs = global_time + t
    bend_angle = max_bend_angle * (0.5 + 0.5 * np.sin(2 * np.pi * bend_freq * t_abs))
    alpha_t = np.clip(bend_angle / 120.0, 0.0, 0.92)
    
    gamma1 = 2000 * (x1**2 - 0.01)
    gamma2 = 2000 * (x2**2 - 0.01)
    common_feedback = coupling * (dx1 + dx2)
    effective_pressure = pressure * (1.0 - 0.2 * alpha_t)
    
    ddx1 = -gamma1*dx1 - (k_left**2)*x1 + effective_pressure - common_feedback
    ddx2 = -gamma2*dx2 - (k_right**2)*x2 + effective_pressure - common_feedback
    
    return [dx1, ddx1, dx2, ddx2]

# 3. Поток живой генерации звука
def audio_stream_loop():
    global y_state, is_playing
    global current_kl, current_kr, current_p, current_c, current_max_bend, current_bend_freq
    
    global_time = 0.0
    y_prev_filter = 0.0 # Память акустического фильтра шеи
    
    with sd.OutputStream(samplerate=SAMPLE_RATE, channels=1, dtype='float32') as stream:
        while is_playing:
            # ЖИВОЕ ВИБРАТО (Нервные импульсы птицы 7 Гц)
            vibrato = 1.0 + 0.08 * np.sin(2 * np.pi * 7.2 * global_time)
            mod_kl = current_kl * vibrato
            mod_kr = current_kr * vibrato
            
            # Расчет физики текущего кадра
            sol = solve_ivp(syrinx_core, T_SPAN, y_state, 
                            args=(mod_kl, mod_kr, current_p, current_c, current_max_bend, current_bend_freq, global_time), 
                            t_eval=T_EVAL, method='RK45')
            
            # 1. ИСПРАВЛЕНИЕ КООРДИНАТ: Берем строго ПОСЛЕДНИЕ ЧИСЛА из каждой строки
            y_state = [sol.y[0, -1], sol.y[1, -1], sol.y[2, -1], sol.y[3, -1]]
            
            # 2. ИСПРАВЛЕНИЕ АУДИО: Складываем строго одномерные векторы смещения левой (0) и правой (2) мембран
            raw_chunk = np.tanh(3.0 * (sol.y[0, :] + sol.y[2, :])) 
            
            # Акустический фильтр шеи по Илюхину
            bend_now = current_max_bend * (0.5 + 0.5 * np.sin(2 * np.pi * current_bend_freq * global_time))
            alpha_now = np.clip(bend_now / 120.0, 0.0, 0.94)
            
            filtered_chunk = np.zeros_like(raw_chunk)
            for i in range(len(raw_chunk)):
                filtered_chunk[i] = (1.0 - alpha_now) * raw_chunk[i] + alpha_now * y_prev_filter
                y_prev_filter = filtered_chunk[i]
            
            # Нормализация
            max_val = np.max(np.abs(filtered_chunk))
            if max_val > 0:
                filtered_chunk = (filtered_chunk / max_val) * 0.25
            
            # ГАРАНТИЯ МОНО-КАНАЛА: Выпрямляем массив в плоский вектор и делаем его вертикальным для sounddevice
            mono_signal = filtered_chunk.flatten().astype('float32').reshape(-1, 1)
            
            # Отправляем в динамики
            stream.write(mono_signal)
            global_time += CHUNK_DURATION

# 4. Интерфейс
fig, ax = plt.subplots(figsize=(10, 5))
plt.subplots_adjust(bottom=0.45)
ax.text(0.1, 0.5, "ФИЗИЧЕСКИЙ СИНТЕС СИРИНКСА (ОБЕРТОНЫ АКТИВИРОВАНЫ)\n\nНажмите СТАРТ и плавно меняйте параметры.\nЗвук стал мягким и певчим.", 
        fontsize=12, ha='left', va='center', color='darkgreen', weight='bold')
ax.axis('off')

# Размещение слайдеров
ax_kl        = plt.axes([0.3, 0.35, 0.55, 0.03])
ax_kr        = plt.axes([0.3, 0.30, 0.55, 0.03])
ax_p         = plt.axes([0.3, 0.25, 0.55, 0.03])
ax_c         = plt.axes([0.3, 0.20, 0.55, 0.03])
ax_max_bend  = plt.axes([0.3, 0.15, 0.55, 0.03])
# ax_bend_freq = plt.axes([0.3, 0.10, 0.03, 0.03]) # Исправлена координата
ax_bend_freq = plt.axes([0.3, 0.10, 0.55, 0.03])

s_kl        = Slider(ax_kl, 'Натяжение Левой', 1000.0, 6000.0, valinit=current_kl, valfmt='%0.0f')
s_kr        = Slider(ax_kr, 'Натяжение Правой', 1000.0, 6000.0, valinit=current_kr, valfmt='%0.0f')
s_p         = Slider(ax_p, 'Давление легких', 50.0, 1500.0, valinit=current_p, valfmt='%0.0f')
s_c         = Slider(ax_c, 'Связь (Трахея)', 0.0, 300.0, valinit=current_c, valfmt='%0.0f')
s_max_bend  = Slider(ax_max_bend, 'Макс. Изгиб Шеи', 0.0, 90.0, valinit=current_max_bend, valfmt='%0.0f°')
s_bend_freq = Slider(ax_bend_freq, 'Скорость кивков (Гц)', 1.0, 10.0, valinit=current_bend_freq, valfmt='%0.1f Гц')

def update_params(val):
    global current_kl, current_kr, current_p, current_c, current_max_bend, current_bend_freq
    current_kl, current_kr = s_kl.val, s_kr.val
    current_p, current_c = s_p.val, s_c.val
    current_max_bend, current_bend_freq = s_max_bend.val, s_bend_freq.val

s_kl.on_changed(update_params)
s_kr.on_changed(update_params)
s_p.on_changed(update_params)
s_c.on_changed(update_params)
s_max_bend.on_changed(update_params)
s_bend_freq.on_changed(update_params)

ax_btn = plt.axes([0.42, 0.02, 0.16, 0.05])
btn = Button(ax_btn, 'СТАРТ / СТОП')

def toggle_playback(event):
    global is_playing
    if not is_playing:
        is_playing = True
        t = threading.Thread(target=audio_stream_loop)
        t.daemon = True
        t.start()
    else:
        is_playing = False

btn.on_clicked(toggle_playback)
plt.show()
