import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtChart import QChart, QChartView, QScatterSeries, QValueAxis
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtCore import Qt, QTimer
import serial
import re
import time

# Separate series for each state
closed_series = QScatterSeries()
closed_series.setMarkerShape(QScatterSeries.MarkerShapeCircle)
closed_series.setColor(Qt.green)  # Green for closed state
closed_series.setBorderColor(Qt.green)  # Green border for closed state
closed_series.setMarkerSize(7.0)

open_series = QScatterSeries()
open_series.setMarkerShape(QScatterSeries.MarkerShapeCircle)
open_series.setColor(Qt.red)  # Red for open state
open_series.setBorderColor(Qt.red)  # Red border for open state
open_series.setMarkerSize(7.0)

# Open serial port
ser = serial.Serial('COM13', 115200)

start_time = time.time()

def read_serial():
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
            
            if switch_state == "Closed":
                closed_series.append(elapsed_time, pressure_psi)
            else:
                open_series.append(elapsed_time, pressure_psi)
            
            # Expand x-axis range by 100 if the newest point's x value exceeds current max x value
            if elapsed_time > chart.axisX().max():
                new_max = chart.axisX().max() + 100
                chart.axisX().setRange(chart.axisX().min(), new_max)
            
            chart.update()
            app.processEvents()

def setup_chart():
    chart = QChart()
    chart.addSeries(closed_series)
    chart.addSeries(open_series)
    
    chart.createDefaultAxes()
    chart.setAnimationOptions(QChart.AllAnimations)
    chart.legend().hide()
    chart.setTitle('Pressure Data')
    chart.axisY().setRange(0.3, 0.6)
    chart.axisX().setRange(0, 100)
    
    # Using predefined chart theme that provides white axis labels
    chart.setTheme(QChart.ChartThemeDark)

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
