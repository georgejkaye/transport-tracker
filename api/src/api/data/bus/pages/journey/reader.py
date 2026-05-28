from datetime import date, datetime, time
from typing import Optional

import selenium.webdriver.support.ui as ui
from api.data.bus.pages.journey.classes import BustimesJourney, BustimesJourneyCall
from api.utils.times import get_datetime_after_start_datetime
from bs4 import BeautifulSoup
from bs4.element import Tag
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options


def get_bustimes_journey_url(bustimes_journey_id: int) -> str:
    return f"https://bustimes.org/journeys/{bustimes_journey_id}"


def get_datetime_from_cell(
    run_date: date, previous_datetime: Optional[datetime], cell: Tag
) -> Optional[datetime]:
    cell_text = cell.getText(strip=True)
    if cell_text[2] != ":":
        return None
    hours = cell_text[0:2]
    if not hours.isnumeric():
        return None
    minutes = cell_text[3:5]
    if not minutes.isnumeric():
        return None
    return get_datetime_after_start_datetime(
        run_date, previous_datetime, time(int(hours), int(minutes))
    )


def get_bustimes_journey_call(
    run_date: date,
    previous_call_datetime: Optional[datetime],
    first_row: Tag,
    second_row: Optional[Tag],
) -> Optional[BustimesJourneyCall]:
    first_row_cells = first_row.find_all("td")
    stop_cell = first_row_cells[0]

    first_plan_cell = first_row_cells[1]

    if not isinstance(first_plan_cell, Tag):
        return None

    first_plan_datetime = get_datetime_from_cell(
        run_date, previous_call_datetime, first_plan_cell
    )

    if second_row is None:
        plan_arr = None
        plan_dep = first_plan_datetime
    else:
        second_row_cells = first_row.find_all("td")
        second_plan_cell = second_row_cells[0]

        if not isinstance(second_plan_cell, Tag):
            return None

        plan_arr = first_plan_datetime
        plan_dep = get_datetime_from_cell(
            run_date, previous_call_datetime, second_plan_cell
        )

    if isinstance(stop_cell, Tag):
        stop_a = stop_cell.find("a")
        if stop_a is not None and isinstance(stop_a, Tag):
            stop_href = stop_a.get("href")
            stop_name = stop_a.get_text(strip=True)
            if stop_href is not None and isinstance(stop_href, str):
                return BustimesJourneyCall(
                    int(stop_href[7:]), stop_name, plan_arr, None, plan_dep, None
                )
    return None


def read_bustimes_journey(
    run_date: date, bustimes_journey_id: int
) -> Optional[BustimesJourney]:
    options = Options()
    options.add_argument("--headless=new")
    driver = webdriver.Firefox(options=options)
    driver.get(get_bustimes_journey_url(bustimes_journey_id))
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
    checkboxes = driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"]')
    if len(checkboxes) == 1:
        checkboxes[0].click()

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    rows = soup.find_all("tr")

    stop_rows: list[list[Tag]] = []
    current_stop_rows: list[Tag] = []

    for row in rows[1:]:
        if isinstance(row, Tag):
            current_stop_rows.append(row)
            if (
                (first_cell := row.find("td")) is not None
                and isinstance(first_cell, Tag)
                and first_cell.get("rowspan") is None
            ):
                stop_rows.append(current_stop_rows)
                current_stop_rows = []

    previous_call_datetime = None

    for stop_row in stop_rows:
        if len(stop_row) == 2:
            second_row = stop_row[1]
        else:
            second_row = None
        call = get_bustimes_journey_call(
            run_date, previous_call_datetime, stop_row[0], second_row
        )
        if call is not None:
            previous_call_datetime = call.plan_dep
            print(call)

    driver.quit()


if __name__ == "__main__":
    read_bustimes_journey(datetime(2026, 5, 27), 888060470)
