from abc import abstractmethod
from typing import Callable

from bs4 import BeautifulSoup
from selenium.webdriver.firefox.options import Options
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
