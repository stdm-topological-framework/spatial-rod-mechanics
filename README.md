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
git clone https://github.com/stdm-topological-framework/spatial-rod-mechanics
cd spatial-rod-mechanics

# Install mathematical and network libraries
pip install -r requirements.txt
```

### 2. Running the Interactive Simulation (GUI)
To execute the physical generator with real-time sliders for membrane tension, pressure, and dynamic neck bending, run the visual module:
```bash
python dynamic_syrinx_system.py
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
python spectrogram_vector.py
```

---

## Why This Simulator Focuses on Mechanics, Not Acoustic Aesthetics

A common misconception when running this physical core for the first time is expecting an immediate, highly realistic, organic bird song instead of an electronic-sounding frequency slide. It is critical to understand the architectural boundaries and the true scientific objective of this repository.

### 1. The Core Scientific Objective
The purpose of this framework is to validate **Ilyukhin's non-linear spatial rod equations for inverse parameter estimation (vocal tract tomography)** from real field recordings. It is designed to extract hidden physical states ($k_L, k_R, P, \theta$) from raw wave data. It is a mathematical instrument, not an acoustic wave-table synthesizer.

### 2. The Biomechanical Complexity of Live Vocalizations
In a living avian organism, the acoustic output is not a static result of a simple differential equation. To achieve near-100% biological realism, a model must integrate:
* **Central Nervous System (CNS) Simulation:** Live birds modulate the tension of syringeal muscles (such as the *m. syringealis ventralis*) with microsecond precision via complex neural feedback loops. The brain of the bird continuously drives these parameters like an advanced neuro-controller.
* **Multi-Muscle Coordination:** The avian syrinx contains up to 6 pairs of independent muscles. This repository deliberately reduces these variables to a concentrated symmetric/asymmetric loading framework ($k_L, k_R$) to ensure fast convergence of the Inverse Problem Solver on edge IoT chips.
* **Complex Boundary Acoustics:** Real birds continuously adjust their beak gape, tongue position, and upper esophageal diverticulum volume during a single syllable, creating a dynamic multi-stage acoustic filter.

### 3. Conclusion for Reviewers
This repository delivers the **fundamental mechanical foundation**. It proves that Ilyukhin's exact analytical methods can successfully reverse-engineer raw wave vectors to isolate internal tissue state variables without invasive surgery. Refining the acoustic aesthetics by wrapping this physics core into a neural network that mimics avian muscle control loops is left as an open direction for future laboratory-backed research grants.

---

## The vocalizations of the Rook
The vocalizations of the Rook (Corvus frugilegus) consist of harsh, guttural calls commonly described as a coarse "kaah," which are used primarily for intra-flock communication. These vocalizations vary in intensity, ranging from low-pitched conversational sounds to loud, strident alarm calls. According to sources, the sound is often produced in a rhythmic, repeating pattern during mating displays or while foraging in large groups. More detailed information and audio recordings of the acoustic repertoire of this species can be found at Xeno-canto. (https://xeno-canto.org/species/corvus-frugilegus)

---

## Авторы / Authors

* **Александр Моисеенко** (Moiseenko Aleksandr) — *Разработчик / Исследователь* — [Профиль GitHub] [https://github.com](https://github.com/alekssan8183269-lang)
* **ORCID:** [0009-0006-4124-5954] [https://orcid.org](https://orcid.org/0009-0006-4124-5954)
