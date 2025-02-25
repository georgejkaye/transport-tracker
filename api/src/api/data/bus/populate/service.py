from dataclasses import dataclass
import io
from os import PathLike
from pathlib import Path
import re
import string
import sys
from typing import Optional
import xml.etree.ElementTree as ET
import zipfile

from api.utils.database import connect
from psycopg import Connection

xmlns_re = r"\{(.*)\}.*"


@dataclass
class TransXChangeLineDescription:
    description: str
    vias: list[str]


@dataclass
class TransXChangeLine:
    name: str
    id: str
    outbound_desc: Optional[TransXChangeLineDescription]
    inbound_desc: Optional[TransXChangeLineDescription]


@dataclass
class TransXChangeOperator:
    id: str
    national_code: str
    code: str
    name: str


def get_line_description_from_description_node(
    description_node: ET.Element, namespaces: dict[str, str]
) -> Optional[TransXChangeLineDescription]:
    description_text_node = description_node.find("Description", namespaces)
    if description_text_node is None:
        return None
    description_text = description_text_node.text or ""
    description_vias_node = description_node.find("Vias", namespaces)
    if description_vias_node is None:
        description_vias = []
    else:
        description_vias = []
        for description_via in description_vias_node.findall("Via", namespaces):
            if description_via.text is not None:
                description_vias.append(
                    string.capwords(description_via.text.replace(" to ", " - "))
                )
    return TransXChangeLineDescription(
        string.capwords(description_text), description_vias
    )


def get_line_from_line_node(
    line_node: ET.Element, namespaces: dict[str, str]
) -> Optional[TransXChangeLine]:
    line_id = line_node.attrib["id"]
    line_name_node = line_node.find("LineName", namespaces)
    if line_name_node is None or line_name_node.text is None:
        return None
    line_name = line_name_node.text
    outbound_desc_node = line_node.find("OutboundDescription", namespaces)
    if outbound_desc_node is None:
        outbound_desc = None
    else:
        outbound_desc = get_line_description_from_description_node(
            outbound_desc_node, namespaces
        )
    inbound_desc_node = line_node.find("InboundDescription", namespaces)
    if inbound_desc_node is None:
        inbound_desc = None
    else:
        inbound_desc = get_line_description_from_description_node(
            inbound_desc_node, namespaces
        )
    return TransXChangeLine(line_name, line_id, outbound_desc, inbound_desc)


def get_lines_from_service_node(
    service_node: ET.Element, namespaces: dict[str, str]
) -> list[TransXChangeLine]:
    lines_node = service_node.find("Lines", namespaces)
    if lines_node is None:
        return []
    lines = []
    for line_node in lines_node.findall("Line", namespaces):
        line = get_line_from_line_node(line_node, namespaces)
        if line is not None:
            lines.append(line)
    return lines


def get_services_from_transxchange_node(
    transxchange_node: ET.Element, namespaces: dict[str, str]
) -> list[TransXChangeLine]:
    services_node = transxchange_node.find("Services", namespaces)
    if services_node is None:
        return []
    service_nodes = services_node.findall("Service", namespaces)
    services = []
    for service_node in service_nodes:
        lines = get_lines_from_service_node(service_node, namespaces)
        services = services + lines
    return services


def get_operator_from_transxchange_node(
    transxchange_node: ET.Element, namespaces: dict[str, str]
) -> Optional[TransXChangeOperator]:
    operators_node = transxchange_node.find("Operators", namespaces)
    if operators_node is None:
        return None
    operator_node = operators_node.find("Operator", namespaces)
    if operator_node is None:
        return None
    bods_operator_id = operators_node.attrib["id"]
    operator_code = operator_node.find("OperatorCode", namespaces)
    if operator_code is None or operator_code.text is None:
        return None
    national_operator_code = operator_node.find(
        "NationalOperatorCode", namespaces
    )
    if national_operator_code is None or national_operator_code.text is None:
        return None
    operator_short_name = operator_node.find("OperatorShortName", namespaces)
    if operator_short_name is None or operator_short_name.text is None:
        return None
    return TransXChangeOperator(
        bods_operator_id,
        national_operator_code.text,
        operator_code.text,
        string.capwords(operator_short_name.text),
    )


def get_operator_and_lines_from_transxchange_node(
    transxchange_node: ET.Element, namespaces: dict[str, str]
) -> Optional[list[tuple[TransXChangeOperator, TransXChangeLine]]]:
    operator = get_operator_from_transxchange_node(
        transxchange_node, namespaces
    )
    if operator is None:
        return None
    lines = get_services_from_transxchange_node(transxchange_node, namespaces)
    return [(operator, line) for line in lines]


def get_transxchange_namespaces(root: ET.Element) -> dict[str, str]:
    namespace_match = re.match(xmlns_re, root.tag)
    if namespace_match is None:
        namespace = ""
    else:
        namespace = namespace_match.group(1)
    return {"": namespace}


def insert_services(
    conn: Connection,
    services: list[tuple[TransXChangeOperator, TransXChangeLine]],
):
    operator_values = []
    service_values = []
    via_values = []
    for operator, service in services:
        operator_values.append(
            (operator.name, operator.code, operator.national_code)
        )
        service_values.append(
            (
                service.name,
                service.id,
                operator.national_code,
                (
                    None
                    if service.outbound_desc is None
                    else service.outbound_desc.description
                ),
                (
                    None
                    if service.inbound_desc is None
                    else service.inbound_desc.description
                ),
            )
        )
        if (
            service.outbound_desc is not None
            and service.outbound_desc.vias is not None
        ):
            for i, via in enumerate(service.outbound_desc.vias):
                via_values.append(
                    (
                        service.id,
                        True,
                        via,
                        i,
                    )
                )
        if (
            service.inbound_desc is not None
            and service.inbound_desc.vias is not None
        ):
            for i, via in enumerate(service.inbound_desc.vias):
                via_values.append(
                    (
                        service.id,
                        False,
                        via,
                        i,
                    )
                )

    conn.execute(
        """SELECT InsertTransXChangeBusData(
            %s::BusOperatorInData[],
            %s::BusServiceInData[],
            %s::BusServiceViaInData[]
        )""",
        [operator_values, service_values, via_values],
    )
    conn.commit()


def extract_data_from_bods_xml(
    xml: str,
) -> Optional[list[tuple[TransXChangeOperator, TransXChangeLine]]]:
    root = ET.fromstring(xml)
    namespaces = get_transxchange_namespaces(root)
    return get_operator_and_lines_from_transxchange_node(root, namespaces)


def extract_data_from_bods_zipfile(
    zip: zipfile.ZipFile,
) -> list[tuple[TransXChangeOperator, TransXChangeLine]]:
    data = []
    print("")
    print("Found following files")
    print("")
    for file_name in zip.namelist():
        print(f"\t{file_name}")
    print("")
    for file_name in zip.namelist():
        file_path = zipfile.Path(zip, file_name)
        file_extension = file_path.suffix
        if file_extension == ".zip":
            print(f"Recursing into {file_name}")
            with zip.open(file_name) as child_zip:
                child_filedata = io.BytesIO(child_zip.read())
                with zipfile.ZipFile(child_filedata) as child_zipfile:
                    child_data = extract_data_from_bods_zipfile(child_zipfile)
                    data = data + child_data
        elif file_extension == ".xml":
            print(f"Extracting data from {file_name}")
            xml = file_path.read_text()
            file_data = extract_data_from_bods_xml(xml)
            if file_data is not None:
                data = data + file_data
    return data


def extract_data_from_bods_zip(
    zip_path: str | Path,
) -> list[tuple[TransXChangeOperator, TransXChangeLine]]:
    with zipfile.ZipFile(zip_path) as zip:
        return extract_data_from_bods_zipfile(zip)


if __name__ == "__main__":
    file_path = sys.argv[1]
    data = extract_data_from_bods_zip(file_path)
    with connect("transport", "transport", "transport", "localhost") as (
        conn,
        _,
    ):
        insert_services(conn, data)
