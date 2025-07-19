import re
from time import sleep
from datetime import datetime
from typing import Dict, Any
from phonenumbers import PhoneNumberMatcher
from PyQt6.QtCore import QObject, pyqtSignal
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, Locator

from src.robot import selectors
from src.my_types import TaskInfo, WorkerSignals
from src.services.result_service import Result_Service
from src.services.ignore_phonenumber_service import IgnorePhoneNumber_Service
from src.services.ignore_uid_service import IgnoreUID_Service
from src.my_constants import LAUNCHING, SCRAPING


def on_launching(
    page: Page, task_info: TaskInfo, signals: WorkerSignals, services: Dict[str, Any]
):
    signals.info_signal.emit(f"{task_info.dir_name} Launching ...")
    page.wait_for_event("close", timeout=0)
    signals.info_signal.emit(f"{task_info.dir_name} Closed!")
    return True


def on_scraper(
    page: Page, task_info: TaskInfo, signals: WorkerSignals, services: Dict[str, Any]
):

    def get_groups():
        try:
            page.goto("https://www.facebook.com/groups/feed/", timeout=60_000)
            signals.info_signal.emit("Successfully navigated to general groups page.")
        except PlaywrightTimeoutError as e:
            return

        signals.info_signal.emit(
            "Waiting for group sidebar to load (if loading icon is present)."
        )
        sidebar_locator = page.locator(
            f"{selectors.S_NAVIGATION}:not({selectors.S_BANNER} {selectors.S_NAVIGATION})"
        )

        group_locators = sidebar_locator.first.locator(
            "a[href^='https://www.facebook.com/groups/']"
        )

        loading_attempt = 0
        max_loading_attempts = 10
        while (
            sidebar_locator.first.locator(selectors.S_LOADING).count()
            and loading_attempt < max_loading_attempts
        ):
            loading_attempt += 1
            signals.info_signal.emit("Loading indicator detected in sidebar")
            _loading_element = sidebar_locator.first.locator(selectors.S_LOADING)
            try:
                sleep(3)
                _loading_element.first.scroll_into_view_if_needed(timeout=100)
                signals.info_signal.emit("Loading indicator scrolled into view.")
            except PlaywrightTimeoutError as e:
                signals.info_signal.emit(
                    "ERROR: Timeout while scrolling loading indicator. Details: {str(e)}. Exiting wait loop."
                )
                break
            except Exception as ex:
                signals.info_signal.emit(
                    f"ERROR: An unexpected error occurred while scrolling loading indicator. Details: {str(ex)}. Exiting wait loop."
                )
                break
        if loading_attempt >= max_loading_attempts:
            signals.info_signal.emit(
                f"WARNING: Exceeded maximum loading wait attempts ({max_loading_attempts}). Continuing without full sidebar load confirmation."
            )
        else:
            signals.info_signal.emit(
                "Group sidebar loaded or no loading indicator found."
            )

        group_locators = sidebar_locator.first.locator(
            "a[href^='https://www.facebook.com/groups/']"
        )
        group_urls = [
            href
            for group_locator in group_locators.all()
            if (href := group_locator.get_attribute("href")) is not None
        ]
        signals.info_signal.emit(f"Found {len(group_urls)} group URLs.")
        if not group_urls:
            signals.info_signal.emit(
                "WARNING: No group URLs could be retrieved. No groups to post in."
            )
            return False
        return group_urls

    print(get_groups())


ACTION_MAP = {
    LAUNCHING: on_launching,
    SCRAPING: on_scraper,
}
