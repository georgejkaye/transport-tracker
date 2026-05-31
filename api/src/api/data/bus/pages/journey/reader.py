from datetime import date, datetime, time, timedelta
from typing import Optional

import selenium.webdriver.support.ui as ui
from api.data.bus.pages.journey.classes import (
    BustimesJourney,
    BustimesJourneyCall,
    BustimesJourneyVehicle,
)
from api.data.selenium.driver import Driver
from bs4 import BeautifulSoup
from bs4.element import Tag
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver


def get_bustimes_journey_url(bustimes_journey_id: int) -> str:
    return f"https://bustimes.org/journeys/{bustimes_journey_id}"


def get_datetime_from_cell(
    board_date: date,
    boarded: bool,
    previous_datetime: Optional[datetime],
    cell: Tag,
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
    call_time_with_board_date = datetime.combine(
        board_date, time(int(hours), int(minutes))
    )
    if previous_datetime is not None:
        if boarded and call_time_with_board_date < previous_datetime:
            return call_time_with_board_date + timedelta(days=1)
        if (
            not boarded
            and call_time_with_board_date - timedelta(days=1) > previous_datetime
        ):
            return call_time_with_board_date - timedelta(days=1)
    return call_time_with_board_date


def get_plan_and_act_datetime_from_row(
    board_date: date,
    boarded: bool,
    first_plan: Optional[datetime],
    first_act: Optional[datetime],
    row: Tag,
    first_time_cell_index: int,
) -> tuple[Optional[datetime], Optional[datetime]]:
    cells = row.find_all("td")
    plan_cell = cells[first_time_cell_index]
    if not isinstance(plan_cell, Tag):
        plan_datetime = None
    else:
        plan_datetime = get_datetime_from_cell(
            board_date, boarded, first_plan, plan_cell
        )
    if len(cells) == first_time_cell_index + 2:
        act_cell = cells[first_time_cell_index + 1]
        if not isinstance(act_cell, Tag):
            act_datetime = None
        else:
            act_datetime = get_datetime_from_cell(
                board_date, boarded, first_act, act_cell
            )
    else:
        act_datetime = None
    return (plan_datetime, act_datetime)


def get_bustimes_journey_call(
    board_date: date,
    boarded: bool,
    board_atco: str,
    first_plan: Optional[datetime],
    first_act: Optional[datetime],
    first_row: Tag,
    second_row: Optional[Tag],
) -> Optional[BustimesJourneyCall]:
    first_row_cells = first_row.select("td")
    stop_cell = first_row_cells[0]

    stop_a = stop_cell.select_one("a")
    if stop_a is None:
        return None

    stop_href = stop_a.get("href")
    if stop_href is None or not isinstance(stop_href, str):
        return None
    stop_atco = stop_href[7:]
    stop_name = stop_a.get_text(strip=True)

    if stop_atco == board_atco:
        boarded = True

    (first_plan, first_act) = get_plan_and_act_datetime_from_row(
        board_date, boarded, first_plan, first_act, first_row, 1
    )
    if second_row is None:
        plan_arr = None
        act_arr = None
        plan_dep = first_plan
        act_dep = first_act
    else:
        plan_arr = first_plan
        act_arr = None
        (plan_dep, _) = get_plan_and_act_datetime_from_row(
            board_date, boarded, first_plan, first_act, second_row, 0
        )
        act_dep = first_act

    return BustimesJourneyCall(
        stop_atco, stop_name, plan_arr, act_arr, plan_dep, act_dep
    )


def get_call_row_lists(page_soup: BeautifulSoup) -> list[list[Tag]]:
    rows = page_soup.find_all("tr")
    call_rows: list[list[Tag]] = []
    current_call_rows: list[Tag] = []
    for row in rows[1:]:
        if isinstance(row, Tag):
            current_call_rows.append(row)
            if (
                (first_cell := row.find("td")) is not None
                and isinstance(first_cell, Tag)
                and first_cell.get("rowspan") is None
            ):
                call_rows.append(current_call_rows)
                current_call_rows = []
    return call_rows


def get_bustimes_calls(
    board_date: date, board_atco: str, call_rows: list[list[Tag]]
) -> list[BustimesJourneyCall]:
    previous_plan = None
    previous_act = None
    calls: list[BustimesJourneyCall] = []
    boarded = False
    for call_row in call_rows:
        if len(call_row) == 2:
            second_row = call_row[1]
        else:
            second_row = None
        call = get_bustimes_journey_call(
            board_date,
            boarded,
            board_atco,
            previous_plan,
            previous_act,
            call_row[0],
            second_row,
        )
        if call is not None:
            if call.stop_id == board_atco:
                boarded = True
            previous_plan = call.plan_dep
            previous_act = call.act_dep
            calls.append(call)
    return calls


def get_bustimes_journey_vehicle(
    page_soup: BeautifulSoup,
) -> Optional[BustimesJourneyVehicle]:
    vehicle_div = page_soup.select_one(".contact-details div:nth-child(1)")
    if not isinstance(vehicle_div, Tag):
        return None
    bustimes_vehicle_a = vehicle_div.select_one("dd a")
    if bustimes_vehicle_a is None:
        return None
    bustimes_vehicle_a_href = bustimes_vehicle_a.get("href")
    if bustimes_vehicle_a_href is None or not isinstance(bustimes_vehicle_a_href, str):
        return None
    else:
        bustimes_id = bustimes_vehicle_a_href.split("/")[2].split("?")[0]
    numberplate_element = bustimes_vehicle_a.select_one("span")
    if numberplate_element is None:
        return None
    else:
        identifier_element = numberplate_element.previous_sibling
        if identifier_element is None:
            identifier = None
        else:
            identifier = identifier_element.text.strip()
        numberplate = numberplate_element.text.strip()
    return BustimesJourneyVehicle(bustimes_id, identifier, numberplate)


def setup_bustimes_journey_page(driver: WebDriver):
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


def get_bustimes_journey_trip_id_and_block(
    page_soup: BeautifulSoup,
) -> Optional[tuple[int, str]]:
    block_div = page_soup.select_one(".contact-details div:nth-child(2)")
    if block_div is None:
        return None
    block_a = block_div.select_one("dd a")
    if block_a is None:
        return None
    block_a_href = block_a.get("href")
    if block_a_href is None or not isinstance(block_a_href, str):
        return None
    trip_id = int(block_a_href.split("/")[2])
    block = block_a.text
    return (trip_id, block)


def get_bustimes_journey(
    driver: Driver, board_date: date, board_atco: str, bustimes_journey_id: int
) -> Optional[BustimesJourney]:
    page_soup = driver.get_page_html(
        get_bustimes_journey_url(bustimes_journey_id), setup_bustimes_journey_page
    )
    stop_rows = get_call_row_lists(page_soup)
    calls = get_bustimes_calls(board_date, board_atco, stop_rows)
    vehicle = get_bustimes_journey_vehicle(page_soup)
    trip_id_and_block_result = get_bustimes_journey_trip_id_and_block(page_soup)
    if trip_id_and_block_result is None:
        return None
    (trip_id, block) = trip_id_and_block_result
    return BustimesJourney(bustimes_journey_id, trip_id, calls, vehicle, block)
