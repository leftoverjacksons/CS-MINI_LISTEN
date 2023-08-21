import numpy as np
import serial
import re
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Serial setup
ser = serial.Serial('COM13', 115200)

# Data lists
plot_data = []
switch_states = []

# Initial Y-axis range
y_min = 0
y_max = 1

def animate(i):
    global y_min, y_max

    if ser.inWaiting():
        line = ser.readline().decode('utf-8').strip()
        match = re.search(r'Pressure \(RAW ADC\):\s+(\d+)', line)
        switch_match = re.search(r'Pressure Switch State: (\w+)', line)
        
        if match and switch_match:
            pressureValue = int(match.group(1))
            voltageOut = (pressureValue / 4095.0) * 3.5
            pressure_kPa = 5.0 * (voltageOut - 1.65)
            pressure_psi = pressure_kPa / 6.89476
                
            switch_state = switch_match.group(1)
                
            print(f"Pressure (PSI): {pressure_psi}, Switch State: {switch_state}")
            
            plot_data.append(pressure_psi)
            switch_states.append(switch_state)

            # Adjust the Y-axis dynamically
            y_min = min(plot_data) - 0.05
            y_max = max(plot_data) + 0.05
            
            # Plotting
            ax.clear()
            ax.set_ylim(y_min, y_max)
            ax.plot(plot_data, label='Pressure (PSI)', color='blue')
            for idx, state in enumerate(switch_states):
                if idx == 0:
                    continue
                if state == "Open":
                    ax.axvspan(idx-1, idx, facecolor='red', alpha=0.2)
                else:
                    ax.axvspan(idx-1, idx, facecolor='green', alpha=0.2)
            ax.legend()

# Creating the figure
fig, ax = plt.subplots()
ani = FuncAnimation(fig, animate, interval=100)
plt.show()
