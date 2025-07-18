from typing import Union, TypeAlias, Optional
from PyQt6.QtWidgets import QDialog
from PyQt6.QtCore import Qt
import webbrowser
from src.ui.dialog_data_ui import Ui_Dialog_Data
from src.models.ignore_phonenumber_model import IgnorePhoneNumber_Model
from src.models.ignore_uid_model import IgnoreUID_Model
from src.models.result_model import Result_Model
from src.my_constants import DATA_TABLES

Model_Type: TypeAlias = Union[IgnorePhoneNumber_Model, IgnoreUID_Model, Result_Model]


class Data_Dialog(QDialog, Ui_Dialog_Data):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.table_name: Optional[str] = None
        self.table_model: Optional[Model_Type] = None
        self.tableView.setWordWrap(True)
        self.tableView.setTextElideMode(Qt.TextElideMode.ElideNone)

    def set_table_model(self, table_name: str):
        self.table_name = table_name
        if self.table_name == DATA_TABLES["Ignore phone"]:
            self.table_model = IgnorePhoneNumber_Model()
        elif self.table_name == DATA_TABLES["Ignore uid"]:
            self.table_model = IgnoreUID_Model()
        elif self.table_name == DATA_TABLES["Results"]:
            self.table_model = Result_Model()
        else:
            raise ValueError(f"Invalid table name '{self.table_name}'")
        self.table_model.select()
        self.tableView.setModel(self.table_model)
        self.tableView.resizeRowsToContents()
        self.tableView.resizeColumnToContents(self.table_model.fieldIndex("article"))
