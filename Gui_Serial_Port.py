import sys
import os
from PyQt6 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import serial
import serial.tools.list_ports

# SerialThread handles serial communication in a separate thread.
class SerialThread(QtCore.QThread):
    data_received = QtCore.pyqtSignal(float)

    def __init__(self, port, baudrate=9600, parent=None):
        super().__init__(parent)
        self.port = port
        self.baudrate = baudrate
        self.running = False
        self.ser = None

    def run(self):
        self.running = True
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
        except Exception as e:
            print("Error opening serial port:", e)
            return

        while self.running:
            try:
                line = self.ser.readline().decode("utf-8").strip()
                if line:
                    try:
                        data = float(line)
                        self.data_received.emit(data)
                    except ValueError:
                        print("Invalid data received:", line)
            except Exception as e:
                print("Serial read error:", e)
        if self.ser and self.ser.is_open:
            self.ser.close()

    def stop(self):
        self.running = False
        self.wait()

# MainWindow builds the modern-looking GUI.
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sensor Data Plotter")
        self.resize(800, 600)
        self.save_directory = None
        self.serial_thread = None
        self.data = []       # Collected sensor data.
        self.plot_data = []  # Data for the real-time plot.
        self.setup_ui()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)

    def setup_ui(self):
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QVBoxLayout(central_widget)

        # Create a pyqtgraph PlotWidget with a dark background.
        self.plot_widget = pg.PlotWidget(title="Real-Time Sensor Data")
        self.plot_widget.setBackground("#2d2d2d")
        main_layout.addWidget(self.plot_widget)
        self.plot_curve = self.plot_widget.plot(
            [],
            pen=pg.mkPen(color=(42, 130, 218), width=2)
        )

        # Create a horizontal layout for the control buttons.
        btn_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(btn_layout)

        self.btn_start = QtWidgets.QPushButton("Start")
        self.btn_start.clicked.connect(self.start_serial)
        btn_layout.addWidget(self.btn_start)

        self.btn_stop = QtWidgets.QPushButton("Stop")
        self.btn_stop.clicked.connect(self.stop_serial)
        btn_layout.addWidget(self.btn_stop)

        self.btn_choose_dir = QtWidgets.QPushButton("Choose Save Directory")
        self.btn_choose_dir.clicked.connect(self.choose_directory)
        btn_layout.addWidget(self.btn_choose_dir)

        self.lbl_dir = QtWidgets.QLabel("No directory chosen")
        btn_layout.addWidget(self.lbl_dir)

        self.btn_save = QtWidgets.QPushButton("Save Data")
        self.btn_save.clicked.connect(self.save_data)
        btn_layout.addWidget(self.btn_save)

    def start_serial(self):
        # Attempt to use the first available serial port.
        if self.serial_thread is None:
            ports = serial.tools.list_ports.comports()
            if ports:
                port = ports[0].device
            else:
                QtWidgets.QMessageBox.critical(self, "Error", "No serial ports found!")
                return
            self.serial_thread = SerialThread(port, 9600)
            self.serial_thread.data_received.connect(self.handle_new_data)
            self.serial_thread.start()
            self.timer.start(100)  # Refresh plot every 100 ms.

    def stop_serial(self):
        if self.serial_thread:
            self.serial_thread.stop()
            self.serial_thread = None
            self.timer.stop()

    def handle_new_data(self, value):
        self.data.append(value)
        self.plot_data.append(value)

    def update_plot(self):
        self.plot_curve.setData(self.plot_data)

    def choose_directory(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.save_directory = directory
            self.lbl_dir.setText(directory)

    def save_data(self):
        if not self.save_directory:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please choose a directory first!")
            return
        file_path = os.path.join(self.save_directory, "sensor_data.txt")
        try:
            with open(file_path, "w") as f:
                for value in self.data:
                    f.write(f"{value}\n")
            QtWidgets.QMessageBox.information(self, "Success", f"Data saved to {file_path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save data: {e}")

    def closeEvent(self, event):
        self.stop_serial()
        event.accept()

# Apply a modern dark theme using the Fusion style and a custom stylesheet.
def set_modern_style(app):
    app.setStyle("Fusion")
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(53, 53, 53))
    palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtCore.Qt.GlobalColor.white)
    palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(35, 35, 35))
    palette.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor(53, 53, 53))
    palette.setColor(QtGui.QPalette.ColorRole.ToolTipBase, QtCore.Qt.GlobalColor.white)
    palette.setColor(QtGui.QPalette.ColorRole.ToolTipText, QtCore.Qt.GlobalColor.white)
    palette.setColor(QtGui.QPalette.ColorRole.Text, QtCore.Qt.GlobalColor.white)
    palette.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor(53, 53, 53))
    palette.setColor(QtGui.QPalette.ColorRole.ButtonText, QtCore.Qt.GlobalColor.white)
    palette.setColor(QtGui.QPalette.ColorRole.BrightText, QtCore.Qt.GlobalColor.red)
    palette.setColor(QtGui.QPalette.ColorRole.Link, QtGui.QColor(42, 130, 218))
    palette.setColor(QtGui.QPalette.ColorRole.Highlight, QtGui.QColor(42, 130, 218))
    palette.setColor(QtGui.QPalette.ColorRole.HighlightedText, QtCore.Qt.GlobalColor.black)
    app.setPalette(palette)
#sd
    # Custom stylesheet for a flat, modern look.
    qss = """
    QMainWindow {
        background-color: #353535;
    }
    QPushButton {
        background-color: #3c3c3c;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 8px 16px;
    }
    QPushButton:hover {
        background-color: #505050;
    }
    QPushButton:pressed {
        background-color: #3c3c3c;
    }
    QLabel {
        color: white;
    }
    """
    app.setStyleSheet(qss)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    set_modern_style(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
