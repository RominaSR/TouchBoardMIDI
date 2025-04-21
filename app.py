import serial
from serial.tools import list_ports
import mido
import json
import threading
import tkinter as tk
from tkinter import ttk
import time

# Load config
with open('config.json') as f:
    config = json.load(f)

baudrate         = config['baudrate']
threshold        = config['threshold']
electrodes       = list(range(12))
note_offset      = config['note_offset']
midi_port_name   = config['midi_port']
default_duration = config['note_duration_ms']
debounce_ms      = config.get('debounce_ms', 300)

# Value mapping
diff_min_map = -10
diff_max_map = 400
note_range = 115

# MIDI port
try:
    midi_out = mido.open_output(midi_port_name)
except IOError:
    print(f"Could not open MIDI port: {midi_port_name}")
    exit()

# Serial port
ports = list_ports.comports()
serial_port = next((p.device for p in ports if 'usbmodem' in p.device or 'USB' in p.description), None)
if not serial_port:
    print("Touch Board not found.")
    exit()

ser = serial.Serial(serial_port, baudrate, timeout=None)
print(f"Connected to {serial_port} @ {baudrate} baud")

# GUI
root = tk.Tk()
root.title("TouchBoard MIDI Monitor")

slider_vars   = {}
label_vars    = {}
checkbox_vars = {}
channel_vars  = {}

threshold_var = tk.IntVar(value=threshold)
tk.Label(root, text="Threshold (min Δ)").grid(row=0, column=0, sticky="w")
ttk.Scale(root, from_=1, to=100, orient="horizontal", variable=threshold_var).grid(row=0, column=1, columnspan=2, sticky="we")
tk.Entry(root, width=5, textvariable=threshold_var).grid(row=0, column=3)

for e in electrodes:
    row = e + 1
    tk.Label(root, text=f"E{e}").grid(row=row, column=0, sticky="w")
    sv = tk.DoubleVar()
    lv = tk.StringVar(value="0")
    cv = tk.BooleanVar(value=(e in config.get("electrodes", [])))
    chv = tk.StringVar(value=str(e+1))

    ttk.Scale(root, from_=diff_min_map, to=diff_max_map, variable=sv, orient="horizontal", length=200).grid(row=row, column=1)
    tk.Label(root, textvariable=lv, width=5).grid(row=row, column=2)
    tk.Checkbutton(root, variable=cv).grid(row=row, column=3)
    tk.Entry(root, width=3, textvariable=chv).grid(row=row, column=4)

    slider_vars[e]   = sv
    label_vars[e]    = lv
    checkbox_vars[e] = cv
    channel_vars[e]  = chv

# Track active notes
active_notes = {}

# MIDI helpers
def send_note_off(note, channel):
    try:
        midi_out.send(mido.Message('note_off', note=note, velocity=0, channel=channel))
    except Exception as e:
        print("Note Off Error:", e)

prev_values      = {e: None for e in electrodes}
last_note_value  = {e: None for e in electrodes}
last_note_time   = {e: 0 for e in electrodes}
note_timers      = {}

def process_diffs(diffs):
    now = time.time() * 1000  # ms

    for e, val in enumerate(diffs):
        slider_vars[e].set(val)
        label_vars[e].set(str(val))

        if not checkbox_vars[e].get():
            continue

        prev = prev_values[e]
        if prev is None:
            prev_values[e] = val
            continue

        delta = abs(val - prev)
        prev_values[e] = val

        if delta < threshold_var.get():
            continue

        scaled = max(min(val, diff_max_map), diff_min_map)
        note = int((scaled - diff_min_map) / (diff_max_map - diff_min_map) * note_range) + note_offset
        note = min(note, 127)

        chan = max(min(int(channel_vars[e].get()) - 1, 15), 0)

        if note == last_note_value[e] and (now - last_note_time[e]) < debounce_ms:
            continue

        # Stop previous note (if different)
        prev_note = last_note_value[e]
        if prev_note is not None and prev_note != note:
            send_note_off(prev_note, chan)

        # Start new note
        last_note_value[e] = note
        last_note_time[e]  = now

        if e in note_timers:
            note_timers[e].cancel()

        duration = max(150, min(1200, int(1200 - delta * 10)))

        try:
            midi_out.send(mido.Message('note_on', note=note, velocity=64, channel=chan))
        except Exception as err:
            print("Note On Error:", err)

        t = threading.Timer(duration / 1000.0, send_note_off, args=[note, chan])
        note_timers[e] = t
        t.start()

def serial_thread():
    while True:
        raw = ser.readline().decode('ascii', errors='ignore').strip()
        if not raw.startswith("DIFF:"):
            continue
        parts = raw[5:].split()
        if len(parts) >= 12:
            diffs = list(map(int, parts[:12]))
            root.after(0, process_diffs, diffs)

threading.Thread(target=serial_thread, daemon=True).start()
root.mainloop()
