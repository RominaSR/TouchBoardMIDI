# 🌿 Touch Board MIDI App 

A lightweight Python app that transforms capacitive sensor data from the Bare Conductive **Touch Board** into MIDI notes in real time.

## 🎛 Features

- Sensor-to-MIDI note mapping with real-time UI
- Adjustable threshold and MIDI routing
- Velocity and duration control based on gesture dynamics
- Works **100% offline** (no internet required)
- Perfect for live performances, interactive installations, and sound design

## ✅ Requirements

- macOS with IAC Driver enabled (for MIDI routing)
- Python 3.8+ and pip
- Bare Conductive Touch Board (connected via USB)

## 🛠 Setup

1. **Clone this repository** or download the files
2. **Connect the Touch Board via USB**
3. **Enable the IAC Driver on macOS**  
   → _Audio MIDI Setup > Window > Show MIDI Studio > Double-click IAC Driver > Check "Device is online"_
4. Use Live or your preferred instruments

4. **Open a terminal** and run:

```bash
pip install -r requirements.txt
python3 app.py
