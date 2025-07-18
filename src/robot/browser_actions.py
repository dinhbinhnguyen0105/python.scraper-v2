from time import sleep
from datetime import datetime
from typing import Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, Locator
import re
from phonenumbers import PhoneNumberMatcher
from src.my_types import TaskInfo, WorkerSignals
from src.robot import selectors
from src.services.result_service import Result_Service
from src.services.ignore_phonenumber_service import IgnorePhoneNumber_Service
from src.services.ignore_uid_service import IgnoreUID_Service


def on_launching(
    page: Page, task_info: TaskInfo, signals: WorkerSignals, services: Dict[str, Any]
):
    signals.info_signal.emit(f"{task_info.dir_name} Launching ...")
    page.wait_for_event("close", timeout=0)
    signals.info_signal.emit(f"{task_info.dir_name} Closed!")
    return True


ACTION_MAP = {
    "launch": on_launching,
}
