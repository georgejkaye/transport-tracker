from abc import abstractmethod
from typing import Callable

from bs4 import BeautifulSoup
from selenium.webdriver.firefox.options import Options

import getpass
import os

# undetected_geckodriver Firefox calls getlogin on init
# but this doesn't work in a docker container
os.getlogin = getpass.getuser

from undetected_geckodriver import Firefox


class Driver:
    @abstractmethod
    def get_page_html(
        self, url: str, action: Callable[[Firefox], None]
    ) -> BeautifulSoup:
        pass


class SeleniumDriver(Driver):
    def get_page_html(
        self, url: str, action: Callable[[Firefox], None]
    ) -> BeautifulSoup:
        options = Options()
        options.add_argument("--headless")
        driver = Firefox(options=options)
        driver.get(url)
        action(driver)
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        driver.quit()
        return soup
