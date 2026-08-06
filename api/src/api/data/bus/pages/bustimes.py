import selenium.webdriver.support.ui as ui
from selenium.webdriver.common.by import By
from undetected_geckodriver import Firefox


def accept_bustimes_cookies(driver: Firefox):
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
