import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtChart import QChart, QChartView, QScatterSeries, QValueAxis,QBarSet, QBarSeries, QBarCategoryAxis
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt, QTimer
import serial
import re
import time
import numpy as np

# Initialize the series to display pressure data
series = QScatterSeries()
series.setMarkerSize(8.0)  # Set the size of the points to 2 pixels

switch_series = QBarSeries()
switch_times = []


# Open serial port
ser = serial.Serial('COM13', 115200)

start_time = time.time()  # Capture the time at which the program starts

def read_serial():
    global series

    if ser.inWaiting():
        line = ser.readline().decode('utf-8').strip()
        # Parse the line to extract the pressure value (raw ADC reading)
        match = re.search(r'Pressure \(RAW ADC\):\s+(\d+)', line)
        if match:
            pressureValue = int(match.group(1))
            # Convert the raw ADC reading to pressure in PSI
            voltageOut = (pressureValue / 4095.0) * 3.5  # Convert ADC reading to voltage
            pressure_kPa = 5.0 * (voltageOut - 1.65)  # Convert voltage to pressure in kPa
            pressure_psi = pressure_kPa / 6.89476  # Convert pressure to PSI
            print(f"Pressure (PSI): {pressure_psi}")

            # Capture the current time and subtract the start time to get time elapsed
            elapsed_time = time.time() - start_time

            # Add pressure value to the series
            series.append(elapsed_time, pressure_psi)

            # Update the range of the x-axis every 100 points
            if len(series.points()) % 100 == 0:
                chart.axisX().setRange(0, elapsed_time + 10)  # Extend range by 10 seconds

            chart.update()  # Force chart to update
            app.processEvents()  # Process all pending events

# Function to setup the chart
def setup_chart():
    chart = QChart()
    chart.addSeries(series)
    chart.createDefaultAxes()
    chart.setAnimationOptions(QChart.AllAnimations)
    chart.legend().hide()
    chart.setTitle('Pressure Data')

    # Set fixed range on Y-axis
    axisY = QValueAxis()
    axisY.setRange(0.3, 0.6)  # Change this to the range you want
    chart.setAxisY(axisY, series)

    # Set initial range on X-axis
    axisX = QValueAxis()
    axisX.setRange(0, 100)  # Change this to the range you want
    chart.setAxisX(axisX, series)

    return chart

app = QApplication(sys.argv)

# Setup chart
chart = setup_chart()
chart_view = QChartView(chart)
chart_view.setRenderHint(QPainter.Antialiasing)

# Setup timer to read serial data every 100 ms
timer = QTimer()
timer.timeout.connect(read_serial)
timer.start(100)

# Show chart
chart_view.show()

# Start Qt event loop
sys.exit(app.exec_())
