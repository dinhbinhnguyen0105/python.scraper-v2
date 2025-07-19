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

    def close_dialog():
        try:
            dialog_locators = page.locator(selectors.S_DIALOG)
            for dialog_locator in dialog_locators.all():
                if dialog_locator.is_visible() and dialog_locator.is_enabled():
                    close_button_locators = dialog_locator.locator(
                        selectors.S_CLOSE_BUTTON
                    )
                    sleep(3)
                    close_button_locators.last.click(timeout=60_000)
                    dialog_locator.wait_for(state="detached", timeout=60_000)
            return True
        except PlaywrightTimeoutError:
            return False

    def find_nearest_ancestor(element: Locator, selector):
        current_element = element
        while current_element:
            elm = current_element.locator(selector).first
        return None

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
        max_loading_attempts = 30
        while (
            sidebar_locator.first.locator(selectors.S_LOADING).count()
            and loading_attempt < max_loading_attempts
        ):
            loading_attempt += 1
            signals.info_signal.emit("Loading indicator detected in sidebar")
            _loading_element = sidebar_locator.first.locator(selectors.S_LOADING)
            try:
                _loading_element.first.scroll_into_view_if_needed(timeout=60_000)
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

    def scraping(url: str):
        page.goto(url=url, timeout=60_000)
        # singal
        close_dialog()
        feed_locators = page.locator(selectors.S_FEED)
        try:
            feed_locators.first.wait_for(state="attached", timeout=60_000)
        except PlaywrightTimeoutError:
            return False
        feed_locator: Locator = feed_locators.first
        if not feed_locator:
            return False

        try:
            post_index = 0
            while post_index < task_info.post_num:
                post = {
                    "user_url": "",
                    "post_url": "",
                    "post_content": "",
                }
                article_locators = feed_locator.locator(selectors.S_ARTICLE)
                article_locators.first.scroll_into_view_if_needed()
                describedby_values = article_locators.first.get_attribute(
                    "aria-describedby"
                )
                article_user_id = article_locators.first.get_attribute(
                    "aria-labelledby"
                )
                (
                    article_info_id,
                    article_message_id,
                    article_content_id,
                    article_reaction_id,
                    article_comment_id,
                ) = describedby_values.split(" ")

                popup_locators = article_locators.first.locator(
                    "[aria-haspopup='menu'][aria-expanded='false']"
                )

                article_user_locator = article_locators.first.locator(
                    f"[id='{article_user_id}']"
                )
                article_info_locator = article_locators.first.locator(
                    f"[id='{article_info_id}']"
                )
                article_message_locator = article_locators.first.locator(
                    f"[id='{article_message_id}']"
                )
                article_content_locator = article_locators.first.locator(
                    f"[id='{article_content_id}']"
                )
                article_reaction_locator = article_locators.first.locator(
                    f"[id='{article_reaction_id}']"
                )
                article_comment_locator = article_locators.first.locator(
                    f"[id='{article_comment_id}']"
                )

                try:
                    article_user_locator.first.wait_for(
                        state="attached", timeout=1_000
                    )
                    article_user_locator.scroll_into_view_if_needed()
                    article_user_locator.highlight()
                    article_user_url_locator = article_user_locator.first.locator(
                        "a"
                    )
                    article_user_url_locator.first.hover()
                    sleep(0.5)
                    user_url = article_user_url_locator.first.get_attribute(
                        "href",
                        timeout=1_000,
                    ).split("?")[0]
                    user_url = (
                        user_url[0:-1] if user_url.endswith("/") else user_url
                    )
                    # TODO request data
                    popup_locators.first.hover()
                    sleep(0.5)
                    uid = user_url.split("/")[-1]
                    services["uid"].
                    if IgnoreUIDService.is_field_value_exists(uid):
                        article_locators.first.evaluate("elm => elm.remove()")
                        signals.sub_progress_signal.emit(
                            task_info.object_name, task_info.post_num, post_index
                        )
                        post_index += 1
                        if post_index > task_info.post_num:
                            break
                        continue
                    else:
                        IgnoreUIDService.create({"value": uid})

                    post["user_url"] = user_url
                except PlaywrightTimeoutError:
                    pass
        except Exception as e:
            print(e)
            return


ACTION_MAP = {
    LAUNCHING: on_launching,
    SCRAPING: on_scraper,
}
