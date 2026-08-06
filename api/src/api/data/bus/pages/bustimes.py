import selenium.webdriver.support.ui as ui
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver


def accept_bustimes_cookies(driver: WebDriver):
    wait = ui.WebDriverWait(driver, 10)

    while True:
        try:
            accept_button = wait.until(
                lambda driver: driver.find_element(By.ID, "accept-btn")
            )
            accept_button.click()
            break
        except:
            pass
