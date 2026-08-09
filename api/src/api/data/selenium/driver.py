import getpass
import os
from abc import abstractmethod
from typing import Any, Callable

from bs4 import BeautifulSoup
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.remote.webdriver import WebDriver

# undetected_geckodriver Firefox calls getlogin on init
# but this doesn't work in a docker container
os.getlogin = getpass.getuser

from undetected_geckodriver import Firefox  # type: ignore


def do_nothing(driver: WebDriver):
    pass


class Driver:
    @abstractmethod
    def get_page_html(
        self, url: str, action: Callable[[WebDriver], None] = do_nothing
    ) -> BeautifulSoup:
        pass


class SeleniumDriver(Driver):
    def __init__(self):
        options = Options()
        options.add_argument("--headless")
        self.driver = Firefox(options)

    def get_page_html(
        self, url: str, action: Callable[[WebDriver], None] = do_nothing
    ) -> BeautifulSoup:
        self.driver.get(url)
        action(self.driver)
        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        return soup


class DriverManager:
    def __init__(self):
        self.driver = SeleniumDriver()
        pass

    def __enter__(self):
        return self.driver

    def __exit__(
        self, exception_type: Any, exception_value: Any, exception_traceback: Any
    ):
        self.driver.driver.quit()
