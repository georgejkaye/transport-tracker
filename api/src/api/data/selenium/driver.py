from abc import abstractmethod
from typing import Callable

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.webdriver import WebDriver


class Driver:
    @abstractmethod
    def get_page_html(
        self, url: str, action: Callable[[WebDriver], None]
    ) -> BeautifulSoup:
        pass


class SeleniumDriver(Driver):
    def get_page_html(
        self, url: str, action: Callable[[WebDriver], None]
    ) -> BeautifulSoup:
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Firefox(options=options)
        driver.get(url)
        action(driver)
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        driver.quit()
        return soup
