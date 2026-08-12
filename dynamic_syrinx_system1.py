import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from scipy.integrate import solve_ivp
import sounddevice as sd  # ОБЯЗАТЕЛЬНО: pip install sounddevice
import threading
import time

# 1. Глобальные аудио-настройки
SAMPLE_RATE = 22050  
CHUNK_DURATION = 0.05  # Считаем звук микро-порциями по 50 миллисекунд
T_SPAN = (0, CHUNK_DURATION)
T_EVAL = np.linspace(0, CHUNK_DURATION, int(SAMPLE_RATE * CHUNK_DURATION))

# Глобальные переменные для связи ползунков с потоком звука
current_kl = 3200.0
current_kr = 3500.0
current_p = 700.0
current_c = 250.0
current_max_bend = 60.0
current_bend_freq = 4.0

is_playing = False
y_state = [0.01, 0.0, 0.01, 0.0]  # Хранит конечные координаты для бесшовного пения

# 2. Нелинейная система сиринкса (Ядро Илюхина)
def syrinx_core(t, y, k_left, k_right, pressure, coupling, max_bend_angle, bend_freq, global_time):
    x1, dx1, x2, dx2 = y
    
    # Динамический изгиб шеи зависит от абсолютного времени генерации
    t_abs = global_time + t
    bend_angle = max_bend_angle * (0.5 + 0.5 * np.sin(2 * np.pi * bend_freq * t_abs))
    alpha_t = np.clip(bend_angle / 120.0, 0.0, 0.92)
    
    # Физика автоколебаний мембран
    gamma1 = 1500 * (x1**2 - 0.01)
    gamma2 = 1500 * (x2**2 - 0.01)
    common_feedback = coupling * (dx1 + dx2)
    effective_pressure = pressure * (1.0 - 0.2 * alpha_t)
    
    ddx1 = -gamma1*dx1 - (k_left**2)*x1 + effective_pressure - common_feedback
    ddx2 = -gamma2*dx2 - (k_right**2)*x2 + effective_pressure - common_feedback
    
    return [dx1, ddx1, dx2, ddx2]

# 3. Бесконечный поток генерации аудио (Audio Thread)
def audio_stream_loop():
    global y_state, is_playing
    global current_kl, current_kr, current_p, current_c, current_max_bend, current_bend_freq
    
    global_time = 0.0
    
    # Открываем непрерывный аудио-поток на чтение из буфера Python
    with sd.OutputStream(samplerate=SAMPLE_RATE, channels=1, dtype='float32') as stream:
        while is_playing:
            # Решаем уравнения для текущего микро-кусочка в 0.05 сек
            sol = solve_ivp(syrinx_core, T_SPAN, y_state, 
                            args=(current_kl, current_kr, current_p, current_c, current_max_bend, current_bend_freq, global_time), 
                            t_eval=T_EVAL, method='RK45')
            
            # Сохраняем конечную точку для следующей итерации (бесшовный стык волны)
            y_state = [sol.y[0][-1], sol.y[1][-1], sol.y[2][-1], sol.y[3][-1]]
            
            # Генерируем аудио-сигнал кадра
            chunk_signal = sol.y[0] + sol.y[2]
            
            # Динамический фильтр бегущей волны в изогнутой трубе шеи
            # Усредненный коэффициент для текущего куска
            bend_now = current_max_bend * (0.5 + 0.5 * np.sin(2 * np.pi * current_bend_freq * global_time))
            alpha_now = np.clip(bend_now / 120.0, 0.0, 0.95)
            
            # Быстрый фильтр
            filtered_chunk = np.zeros_like(chunk_signal)
            y_prev = 0.0
            for i in range(len(chunk_signal)):
                filtered_chunk[i] = (1.0 - alpha_now) * chunk_signal[i] + alpha_now * y_prev
                y_prev = filtered_chunk[i]
            
            # Нормализация громкости, чтобы защитить динамики
            max_val = np.max(np.abs(filtered_chunk))
            if max_val > 0:
                filtered_chunk = (filtered_chunk / max_val) * 0.3 # Ограничиваем общую громкость на 30%
            
            # Отправляем готовый кусок звука прямо в динамики
            stream.write(filtered_chunk.astype('float32'))
            
            global_time += CHUNK_DURATION

# 4. Создание графического интерфейса Matplotlib
fig, ax = plt.subplots(figsize=(10, 5))
plt.subplots_adjust(bottom=0.45)
ax.text(0.1, 0.5, "БЕСКОНЕЧНОЕ ПЕНИЕ АКТИВИРОВАНО\n\nДвигайте ползунки в реальном времени!\nЗвук меняется на лету.", 
        fontsize=14, ha='left', va='center', color='indigo')
ax.axis('off')

# Размещение слайдеров
ax_kl        = plt.axes([0.3, 0.35, 0.55, 0.03])
ax_kr        = plt.axes([0.3, 0.30, 0.55, 0.03])
ax_p         = plt.axes([0.3, 0.25, 0.55, 0.03])
ax_c         = plt.axes([0.3, 0.20, 0.55, 0.03])
ax_max_bend  = plt.axes([0.3, 0.15, 0.55, 0.03])
ax_bend_freq = plt.axes([0.3, 0.10, 0.55, 0.03])

s_kl        = Slider(ax_kl, 'Натяжение Левой', 1000.0, 8000.0, valinit=current_kl, valfmt='%0.0f')
s_kr        = Slider(ax_kr, 'Натяжение Правой', 1000.0, 8000.0, valinit=current_kr, valfmt='%0.0f')
s_p         = Slider(ax_p, 'Давление легких', 50.0, 2000.0, valinit=current_p, valfmt='%0.0f')
s_c         = Slider(ax_c, 'Связь (Трахея)', 0.0, 1000.0, valinit=current_c, valfmt='%0.0f')
s_max_bend  = Slider(ax_max_bend, 'Макс. Изгиб Шеи', 0.0, 90.0, valinit=current_max_bend, valfmt='%0.0f°')
s_bend_freq = Slider(ax_bend_freq, 'Скорость кивков (Гц)', 1.0, 15.0, valinit=current_bend_freq, valfmt='%0.1f Гц')

# 5. Функции считывания ползунков на лету
def update_params(val):
    global current_kl, current_kr, current_p, current_c, current_max_bend, current_bend_freq
    current_kl = s_kl.val
    current_kr = s_kr.val
    current_p = s_p.val
    current_c = s_c.val
    current_max_bend = s_max_bend.val
    current_bend_freq = s_bend_freq.val

s_kl.on_changed(update_params)
s_kr.on_changed(update_params)
s_p.on_changed(update_params)
s_c.on_changed(update_params)
s_max_bend.on_changed(update_params)
s_bend_freq.on_changed(update_params)

# 6. Логика кнопки СТАРТ / СТОП
ax_btn = plt.axes([0.42, 0.02, 0.16, 0.05])
btn = Button(ax_btn, 'СТАРТ / СТОП')

def toggle_playback(event):
    global is_playing
    if not is_playing:
        is_playing = True
        # Запускаем бесконечный цикл расчёта звука в отдельном фоновом потоке
        t = threading.Thread(target=audio_stream_loop)
        t.daemon = True
        t.start()
        print("[AUDIO] Бесконечный живой синтез запущен!")
    else:
        is_playing = False
        print("[AUDIO] Синтез остановлен.")

btn.on_clicked(toggle_playback)

plt.show()
