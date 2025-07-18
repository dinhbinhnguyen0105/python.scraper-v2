# src/controllers/robot_controller.py
import os
from typing import List
from PyQt6.QtCore import pyqtSignal, QObject, pyqtSlot
from src.my_types import TaskInfo, WorkerSignals
from src.robot.robot_manager import RobotManager


class RobotController(QObject):
    def __init__(self, parent):
        super().__init__(parent)
