# src/controllers/result_controller.py
from PyQt6.QtWidgets import QWidget
from typing import TypeAlias, Union, Any, List
from src.my_types import Result_Type
from src.models.result_model import Result_Model
from src.services.result_service import Result_Service
from src.controllers.base_controller import BaseController


class Result_Controller(BaseController):
    def __init__(self, table_model: Result_Model):
        super().__init__(service=Result_Service(), table_model=table_model)

    def delete(self, ids_to_delete: List[int]) -> bool:
        try:
            self.controller_signals.info.emit(
                f"The records {ids_to_delete} will be deleted."
            )
            if self.service.delete_multiple(ids=ids_to_delete):
                self.controller_signals.success.emit(
                    f"The records {ids_to_delete} will deleted."
                )
                self.refresh_data()
            else:
                self.controller_signals.warning.emit(
                    f"Could not delete records {ids_to_delete}"
                )
        except Exception as e:
            self.controller_signals.error.emit(
                f"An error occurred while deleting the records: {e}"
            )
