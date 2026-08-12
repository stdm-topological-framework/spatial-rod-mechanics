import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from scipy.integrate import solve_ivp
import sounddevice as sd  # Для живого вывода звука (опционально)

# 1. Параметры аудио-движка
SAMPLE_RATE = 22050  # Частота дискретизации (Гц)
DURATION = 0.5       # Длительность симуляции одного кадра (секунды)
T_SPAN = (0, DURATION)
T_EVAL = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION))

# 2. Функция дифференциальных уравнений (Связанный сиринкс по Илюхину)
def syrinx_system(t, y, k_left, k_right, pressure, coupling):
    # y[0] = x1 (левая мембрана), y[1] = dx1/dt
    # y[2] = x2 (правая мембрана), y[3] = dx2/dt
    x1, dx1, x2, dx2 = y
    
    # Нелинейное затухание (сопротивление тканей при сжатии)
    gamma1 = 1000 * (x1**2 - 0.01)
    gamma2 = 1000 * (x2**2 - 0.01)
    
    # Взаимное влияние половин через общее давление в трахеи (coupling)
    common_feedback = coupling * (dx1 + dx2)
    
    # Уравнения пространственных автоколебаний стержней-мембран
    # k_left и k_right имитируют концевое натяжение мышц (жесткость по Илюхину)
    ddx1 = -gamma1*dx1 - (k_left**2)*x1 + pressure - common_feedback
    ddx2 = -gamma2*dx2 - (k_right**2)*x2 + pressure - common_feedback
    
    return [dx1, ddx1, dx2, ddx2]

# 3. Начальные условия (микро-смещение, чтобы запустить колебания)
y0 = [0.01, 0.0, 0.01, 0.0]

# 4. Создание графического интерфейса
fig, (ax_wave, ax_spec) = plt.subplots(2, 1, figsize=(10, 6))
plt.subplots_adjust(bottom=0.35, hspace=0.4)

# Исходные настройки ползунков
init_k_left = 3000   # Жесткость левой мембраны (высота звука 1)
init_k_right = 3200  # Жесткость правой мембраны (высота звука 2)
init_p = 500         # Давление воздуха (громкость/хаос)
init_c = 200         # Сила связи (эффект дуэта)

# Первая симуляция
sol = solve_ivp(syrinx_system, T_SPAN, y0, args=(init_k_left, init_k_right, init_p, init_c), t_eval=T_EVAL, method='RK45')
audio_signal = sol.y[0] + sol.y[2] # Суммарный звук двух мембран

# Отрисовка волны и спектрограммы
line, = ax_wave.plot(T_EVAL[:1000], audio_signal[:1000], color='teal', lw=1.5)
ax_wave.set_title("Форма звуковой волны (первые 1000 отсчетов)")
ax_wave.set_ylim(-1.5, 1.5)
ax_wave.grid(True)

Pxx, freqs, bins, im = ax_spec.specgram(audio_signal, NFFT=256, Fs=SAMPLE_RATE, noverlap=128, cmap='inferno')
ax_spec.set_title("Спектрограмма (Визуальный паспорт голоса)")
ax_spec.set_ylabel("Частота (Гц)")
ax_spec.set_ylim(0, 4000)

# 5. Размещение интерактивных ползунков (Слайдеров)
ax_kl = plt.axes([0.2, 0.22, 0.65, 0.03])
ax_kr = plt.axes([0.2, 0.17, 0.65, 0.03])
ax_p  = plt.axes([0.2, 0.12, 0.65, 0.03])
ax_c  = plt.axes([0.2, 0.07, 0.65, 0.03])

s_kl = Slider(ax_kl, 'Жесткость Левой (Мышцы)', 1000.0, 8000.0, valinit=init_k_left, valfmt='%0.0f')
s_kr = Slider(ax_kr, 'Жесткость Правой (Мышцы)', 1000.0, 8000.0, valinit=init_k_right, valfmt='%0.0f')
s_p  = Slider(ax_p, 'Давление (Легкие)', 50.0, 2000.0, valinit=init_p, valfmt='%0.0f')
s_c  = Slider(ax_c, 'Связь Половин (Трахея)', 0.0, 1000.0, valinit=init_c, valfmt='%0.0f')

# 6. Функция обновления при изменении ползунков
def update(val):
    # Пересчитываем дифференциальные уравнения с новыми параметрами
    sol = solve_ivp(syrinx_system, T_SPAN, y0, args=(s_kl.val, s_kr.val, s_p.val, s_c.val), t_eval=T_EVAL, method='RK45')
    signal = sol.y[0] + sol.y[2]
    
    # Нормализуем звук, чтобы не хрипели колонки
    if np.max(np.abs(signal)) > 0:
        signal = signal / np.max(np.abs(signal))
        
    # Обновляем графики
    line.set_ydata(signal[:1000])
    ax_spec.clear()
    ax_spec.specgram(signal, NFFT=256, Fs=SAMPLE_RATE, noverlap=128, cmap='inferno')
    ax_spec.set_title("Спектрограмма (Визуальный паспорт голоса)")
    ax_spec.set_ylim(0, 4000)
    fig.canvas.draw_idle()
    
    # Воспроизведение звука (если установлена библиотека sounddevice)
    try:
        sd.play(signal, SAMPLE_RATE)
    except NameError:
        pass

s_kl.on_changed(update)
s_kr.on_changed(update)
s_p.on_changed(update)
s_c.on_changed(update)

# Кнопка воспроизведения звука
ax_btn = plt.axes([0.45, 0.01, 0.1, 0.04])
btn = Button(ax_btn, 'ПЕТЬ!')
btn.on_clicked(update)

plt.show()
