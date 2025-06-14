import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from api.utils.database import connect, get_db_connection_data_from_args
from api.utils.interactive import information
from psycopg import Connection


traveline_operators_data_url = "https://www.travelinedata.org.uk/wp-content/themes/desktop/nocadvanced_download.php?reportFormat=xmlFlatFile&allTable%5B%5D=table_noclines&allTable%5B%5D=table_noc_table&submit=Submit"


@dataclass
class TravelineOperator:
    name: str
    national_code: str


def extract_operator_data_from_traveline_xml(
    traveline_xml_path: str,
) -> list[TravelineOperator]:
    root = ET.parse(traveline_xml_path)
    noclines_element = root.find("NOCLines")
    if noclines_element is None:
        return []

    traveline_operators: list[TravelineOperator] = []

    nocline_elements = noclines_element.findall("NOCLinesRecord")
    for nocline_element in nocline_elements:
        mode_element = nocline_element.find("Mode")
        if (
            mode_element is None
            or mode_element.text is None
            or mode_element.text != "Bus"
        ):
            continue

        noc_code_element = nocline_element.find("NOCCODE")
        if noc_code_element is None or noc_code_element.text is None:
            continue
        noc_code = noc_code_element.text

        public_name_element = nocline_element.find("PubNm")
        if public_name_element is None or public_name_element.text is None:
            continue
        public_name = public_name_element.text

        traveline_operator = TravelineOperator(public_name, noc_code)
        traveline_operators.append(traveline_operator)

    return traveline_operators


def insert_operators(conn: Connection, operators: list[TravelineOperator]):
    operator_values = []
    for operator in operators:
        operator_values.append((operator.name, operator.national_code))
    conn.execute(
        "SELECT InsertBusOperators(%s::BusOperatorInData[])", [operator_values]
    )
    conn.commit()


def populate_bus_operators(
    conn: Connection, traveline_xml_path: str
) -> list[TravelineOperator]:
    information("Retrieving bus operators")
    data = extract_operator_data_from_traveline_xml(traveline_xml_path)
    information("Inserting bus operators")
    insert_operators(conn, data)
    return data


if __name__ == "__main__":
    connection_data = get_db_connection_data_from_args()
    with connect(connection_data) as conn:
        populate_bus_operators(conn, sys.argv[5])
