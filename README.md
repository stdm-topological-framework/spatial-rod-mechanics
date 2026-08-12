# Bio-Mechanical Digital Twin of the Avian Syrinx
An analytical Edge-IoT simulator of non-linear syrinx dynamics with time-dependent resonator deformation based on Ilyukhin's elastic rod theory.

## Overview
This repository provides a Physical-Informed AI / Digital Twin framework that models avian vocalization through non-linear mechanics instead of traditional black-box neural networks. 

Unlike standard sound classifiers, this system solves a system of non-linear ordinary differential equations (ODEs) in real-time. It models the left and right membranes of the syrinx as 3D elastic structures subjected to dynamic boundary conditions and variable pressure loads.

---

## Key Scientific Innovatons
* **Ilyukhin's Method Integration:** The vocal tract (trachea) is modeled as a spatially deformable elastic rod. Dynamic neck bending $\kappa = \kappa(s, t)$ acts as a time-dependent acoustic filter.
* **Asymmetric Dual-Oscillator Core:** Simulates the non-linear coupling and aerodynamic feedback between the two independent syrinx membranes with delay parameters.
* **Edge-IoT Telemetry Generation:** Instead of transmitting heavy raw audio files, the system extracts precise physical metrics (Chaos Index, Membrane Asymmetry Factor, Resonance Shifts) and packs them into a lightweight JSON payload on the edge.
  
---

## Mathematical Model
The core oscillation of each membrane is governed by a modified Van der Pol-type system with non-linear damping $\gamma(x)$ and common aerodynamic feedback $P_{common}$:

$$\frac{d^2x}{dt^2} + \gamma(x) \frac{dx}{dt} + \omega^2 x = P_{eff}(t) - \beta(\dot{x}_1 + \dot{x}_2)$$

Where $P_{eff}(t)$ is dynamically scaled by the spatial curvature vector of the trachea under geometric deformation.

---

## Applications
1. **Ecoacoustic Health Diagnostics:** Identifying avian diseases and population aging trends by tracking the `membrane_asymmetry_factor` in reverse-engineered field recordings.
2. **Bio-Inspired Robotics & Soft Actuators:** Control algorithms for flexible medical endoscopes and soft robotic manipulators.
3. **Edge Monitoring Networks:** Deploying lightweight physical models on low-power microcontrollers (STM32/ESP32) for autonomous wilderness deployment.

~~~
├── ilyukhin_core/         # Математическое ядро (уравнения стержней и осцилляторов)
├── applications/
│   ├── bioacoustics/      # Наш симулятор сиринкса и изгиба шеи птицы
│   ├── soft_robotics/     # Симулятор гибкого манипулятора / медицинского зонда
│   └── drill_strings/     # Расчет кручения буровой колонны на глубине
└── README.md              # Главное описание всей платформы
~~~
---
Analytical Digital Twins for Real-Time Edge Continuum Mechanics(Аналитические цифровые двойники для механики сплошных сред на периферийных устройствах в реальном времени).

---

## Scientific Foundation: The Ilyukhin Academic School

The mathematical core of this framework is entirely rooted in the fundamental research of **Professor Alexander Alekseevich Ilyukhin** (Doctor of Physical and Mathematical Sciences), the long-standing Head of the Department of Mathematical Analysis and Geometry at the Taganrog State Pedagogical Institute (TGPI). 

As a direct student and advisee of Professor Ilyukhin, the author developed this computational framework to bridge the gap between traditional Soviet theoretical mechanics (the Don mechanics school) and modern real-time Edge-IoT systems.

### Core Monographs and Theories Applied:
The geometric and constitutive equations inside this repository are numerical implementations of the following landmark works by A.A. Ilyukhin:
1. **"Spatial Problems of the Non-Linear Theory of Elastic Rods" (Prostranstvennye zadachi nelinejnoj teorii uprugih sterzhnej)** — This work provided the exact analytical methods for integrating non-linear differential equations governing three-dimensional elastic deformation under terminal and distributed boundary loads.
2. **"Analytical Mechanics of Spatially Deformable Continuums"** — Utilized to define the moving coordinate systems (Darboux-Frenet frames) that trace the dynamic curvature $\kappa(s, t)$ of the vocal tract and flexible actuators in real-time.

### From Pure Mathematics to Edge Computing:
Professor Ilyukhin was a pure theoretical mathematician who solved the most complex non-linear spatial boundary problems on paper. This repository evolves his analytical heritage by converting exact, heavy closed-form solutions into lightweight, fast-converging ordinary differential equations (ODEs). 

By replacing massive finite-element analysis (FEA) with Ilyukhin's targeted non-linear analytical mechanics, we enable low-power microcontrollers (such as STM32/ESP32) to compute complex continuum mechanics on the edge with zero latency.

---

## Installation and Execution Guide

This framework is built using Python 3.8+. To ensure cross-platform compatibility and eliminate configuration issues, follow the structured setup guide below.

### 1. Environment Setup
Clone the repository and install all required dependencies (including numerical solvers and network modules) via `pip` using the provided configuration file:

```bash
# Clone the repository
git clone https://github.com
cd spatial-rod-mechanics

# Install mathematical and network libraries
pip install -r requirements.txt
```

### 2. Running the Interactive Simulation (GUI)
To execute the physical generator with real-time sliders for membrane tension, pressure, and dynamic neck bending, run the visual module:
```bash
python applications/bioacoustics/gui_app.py
```
*Note: Use the interactive sliders to observe how spatial deformations alter the acoustic spectrum in real-time.*

### 3. Running the Edge-IoT Pipeline (Streaming Telemetry)
To simulate the complete decentralized data ingestion pipeline, you need to execute the server and the transmitter in two separate terminal instances:

* **Step A: Start the Laboratory Ingestion Server** (Listens on port 8080 for incoming physical JSON packets):
  ```bash
  python server.py
  ```
* **Step B: Start the Edge IoT Transmitter** (Solves the non-linear ODEs, extracts metrics, and streams telemetry):
  ```bash
  python iot_transmitter.py
  ```

### 4. Running the Inverse Problem Solver (Audio Verification)
To reverse-engineer a vocalization and extract the hidden mechanical parameters (Tension, Bend, and Feathers absorption), execute the optimization module:
```bash
python applications/bioacoustics/inverse_solver.py
```
