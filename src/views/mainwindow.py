from typing import List
from PyQt6.QtWidgets import QMainWindow, QDialogButtonBox, QWidget
from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator

from src.ui.mainwindow_ui import Ui_MainWindow
from src.views.thread_container_w import ThreadContainer_Widget
from src.views.dialog_data import Data_Dialog
from src.my_constants import DATA_TABLES


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Scraper")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.setup_ui()
        self.setup_events()

        self.thread_num = 0
        self.list_thread_widget: List[ThreadContainer_Widget] = []

    def setup_ui(self):
        self.thread_num_input.setValue(0)
        regex = QRegularExpression("^[a-zA-Z0-9 &,]+$")
        validator = QRegularExpressionValidator(regex)
        self.group_key_input.setValidator(validator)
        self.ignore_group_key_input.setValidator(validator)
        self.group_key_input.setText("thuê, sang")
        self.ignore_group_key_input.setText("trọ")

        self.data_open_btn.setDisabled(True)
        for name, value in DATA_TABLES.items():
            self.data_combobox.addItem(name, value)

    def setup_events(self):
        self.data_combobox.currentIndexChanged.connect(self.on_data_combobox_changed)
        self.data_open_btn.clicked.connect(self.on_data_open)

    def on_data_open(self):
        data_dialog = Data_Dialog(self)
        data_dialog.set_table_model(
            self.data_combobox.itemData(self.data_combobox.currentIndex())
        )
        data_dialog.exec()

    def on_data_combobox_changed(self, index: int):
        if self.data_combobox.itemData(index):
            self.data_open_btn.setEnabled(True)
