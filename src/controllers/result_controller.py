# src/controllers/result_controller.py
from PyQt6.QtWidgets import QWidget
from typing import TypeAlias, Union, Any
from src.my_types import Result_Type
from src.models.result_model import Result_Model
from src.services.result_service import Result_Service
from src.controllers.base_controller import BaseController


class Result_Controller(BaseController):
    def __init__(self, ui_view: Any, table_model: Result_Model):
        super().__init__(service=Result_Service(), table_model=table_model)
        self.ui_view = ui_view
        self.ui_view.delete