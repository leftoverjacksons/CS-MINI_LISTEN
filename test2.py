import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QTimer
import serial
import re
import time

# Lists to hold series for both states
series_open_list = []
series_closed_list = []

# Initial series for both states
series_open = QLineSeries()
series_open.setPen(QPen(QColor("red")))
series_closed = QLineSeries()
series_closed.setPen(QPen(QColor("green")))

# Add initial series to lists
series_open_list.append(series_open)
series_closed_list.append(series_closed)

# Open serial port
ser = serial.Serial('COM13', 115200)

start_time = time.time()
pressure_data = []
last_switch_state = None

def read_serial():
    global series_open, series_closed, last_switch_state

    if ser.inWaiting():
        line = ser.readline().decode('utf-8').strip()
        pressure_match = re.search(r'Pressure \(RAW ADC\):\s+(\d+)', line)
        switch_match = re.search(r'Pressure Switch State: (\w+)', line)
        
        if pressure_match and switch_match:
            pressureValue = int(pressure_match.group(1))
            voltageOut = (pressureValue / 4095.0) * 3.5
            pressure_kPa = 5.0 * (voltageOut - 1.65)
            pressure_psi = pressure_kPa / 6.89476
            
            switch_state = switch_match.group(1)
            
            elapsed_time = time.time() - start_time
            
            # For smoothing the data
            pressure_data.append(pressure_psi)
            if len(pressure_data) > 5:
                pressure_data.pop(0)
            avg_pressure = sum(pressure_data) / len(pressure_data)

            # If switch state changes, create a new series and add it to the chart
            if last_switch_state != switch_state:
                if switch_state == "Open":
                    series_open = QLineSeries()
                    series_open.setPen(QPen(QColor("red")))
                    series_open_list.append(series_open)
                    chart.addSeries(series_open)
                    chart.setAxisX(chart.axisX(), series_open)
                    chart.setAxisY(chart.axisY(), series_open)
                else:
                    series_closed = QLineSeries()
                    series_closed.setPen(QPen(QColor("green")))
                    series_closed_list.append(series_closed)
                    chart.addSeries(series_closed)
                    chart.setAxisX(chart.axisX(), series_closed)
                    chart.setAxisY(chart.axisY(), series_closed)
            
            if switch_state == "Open":
                series_open.append(elapsed_time, avg_pressure)
            else:
                series_closed.append(elapsed_time, avg_pressure)

            last_switch_state = switch_state
            chart.update()
            app.processEvents()

def setup_chart():
    chart = QChart()
    for s in series_open_list:
        chart.addSeries(s)
    for s in series_closed_list:
        chart.addSeries(s)
    
    chart.createDefaultAxes()
    chart.setAnimationOptions(QChart.AllAnimations)
    chart.legend().hide()
    chart.setTitle('Pressure Data')

    axisY = QValueAxis()
    axisY.setRange(0.3, 0.6)
    for s in series_open_list:
        chart.setAxisY(axisY, s)
    for s in series_closed_list:
        chart.setAxisY(axisY, s)

    axisX = QValueAxis()
    axisX.setRange(0, 100)
    for s in series_open_list:
        chart.setAxisX(axisX, s)
    for s in series_closed_list:
        chart.setAxisX(axisX, s)

    return chart

app = QApplication(sys.argv)
chart = setup_chart()
chart_view = QChartView(chart)
chart_view.setRenderHint(QPainter.Antialiasing)

timer = QTimer()
timer.timeout.connect(read_serial)
timer.start(100)

# Create a QMainWindow to nest your QWidget in (needed for the menu and so on)
window = QMainWindow()
window.setCentralWidget(chart_view)
window.show()

# Start Qt event loop
sys.exit(app.exec_())
