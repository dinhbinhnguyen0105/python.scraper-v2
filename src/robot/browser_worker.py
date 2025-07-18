from uuid import uuid4
from playwright.sync_api import sync_playwright
from playwright._impl._errors import TargetClosedError
from undetected_playwright import Tarnished

from PyQt6.QtCore import QRunnable, QObject, pyqtSignal, pyqtSlot
from src.my_types import WorkerSignals
from src.services.result_service import Result_Service
from src.services.ignore_phonenumber_service import IgnorePhoneNumber_Service
from src.services.ignore_uid_service import IgnoreUID_Service
from src.robot.browser_actions import ACTION_MAP


class BrowserWorker(QRunnable):
    def __init__(self, task_info, retry_num: int):
        super().__init__()
        self.task_info = task_info
        self.retry_num = retry_num
        self.worker_signals = WorkerSignals()

        self.setAutoDelete(True)

    def run(self):
        try:
            action_function = ACTION_MAP.get(self.task_info.action_name, None)
            if not action_function:
                return False
            connection_name = f"worker_{uuid4()}"
            result_service = Result_Service(connection_name=connection_name)
            ignore_phonenumber_service = IgnorePhoneNumber_Service(
                connection_name=connection_name
            )
            ignore_uid_service = IgnoreUID_Service(connection_name=connection_name)

            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=self.task_info.user_data_dir,
                    headless=self.task_info.headless,
                    args=["--disable-blink-features=AutomationControlled"],
                    ignore_default_args=["--enable-automation"],
                )

                Tarnished.apply_stealth(context)
                page = context.new_page()
                action_function(
                    page=page,
                    task_info=self.task_info,
                    signals=self.worker_signals,
                    services={
                        "uid": ignore_uid_service,
                        "phone_number": ignore_phonenumber_service,
                        "result": result_service,
                    },
                )
        except TargetClosedError:
            return
        except Exception as e:
            self.worker_signals.error_signal.emit(
                self.task_info, self.retry_num, str(e)
            )
        finally:
            result_service.remove_database()
            ignore_phonenumber_service.remove_database()
            ignore_uid_service.remove_database()
            self.worker_signals.finished_signal.emit(self.task_info, self.retry_num)
            return
