from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.Qt import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *

import pyqt5_fugueicons as fugue
from main_window import *

class CarPlateInfoViewerWindow(QMainWindow):
    def __init__(self, html, type):
        super().__init__()

        self.setWindowIcon(fugue.icon("information", size=16, fallback_size=True))

        # 내용 추가

        self.show()

class ImageViewerWindow(QMainWindow):
    def __init__(self, items):
        super().__init__()
        self.setWindowTitle("Image and Data Viewer")
        
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        self.image_label = QLabel()
        layout.addWidget(self.image_label)
        
        self.data_label = QLabel()
        layout.addWidget(self.data_label)
        
        central_widget.setLayout(layout)
        
        pixmap = items["image"]
        self.show_image(pixmap)
        
        data_text = f"is_ev: {items['is_ev']}\nis_one_line: {items['is_one_line']}\nis_two_line: {items['is_two_line']}"
        self.show_data(data_text)
        
    def show_image(self, pixmap):
        self.image_label.setPixmap(pixmap)
        self.image_label.adjustSize()
        
    def show_data(self, data_text):
        self.data_label.setText(data_text)

class ResultDialog(QDialog):
    def __init__(self, items):
        super().__init__()
        self.setWindowTitle("알림")
        
        layout = QVBoxLayout()

        for row, values in items.items():
            row_label = QLabel(f"Row {row}:")
            ev_label = QLabel(f"EV: {values[0]}")
            one_line_label = QLabel(f"One Line: {values[1]}")
            two_line_label = QLabel(f"Two Line: {values[2]}")
            image_label = QLabel()
            image_label.setPixmap(values[3].scaled(self.image_viewer.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            
            layout.addWidget(row_label)
            layout.addWidget(ev_label)
            layout.addWidget(one_line_label)
            layout.addWidget(two_line_label)
            layout.addWidget(image_label)

        widget = QWidget()
        widget.setLayout(layout)
        self.layout = layout
        
        self.setLayout(layout)