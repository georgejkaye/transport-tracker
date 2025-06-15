import re
import string
import zipfile
import io
import xml.etree.ElementTree as ET

from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from api.db.bus.populate.operators import TravelineOperator
from api.utils.interactive import information
from psycopg import Connection

xmlns_re = r"\{(.*)\}.*"

bods_timetables_url = (
    "https://data.bus-data.dft.gov.uk/timetable/download/bulk_archive"
)


@dataclass
class TransXChangeLineDescription:
    description: str
    vias: list[str]


@dataclass
class TransXChangeLine:
    name: str
    id: str
    noc: str
    outbound_desc: Optional[TransXChangeLineDescription]
    inbound_desc: Optional[TransXChangeLineDescription]


def get_line_description_from_description_node(
    description_node: ET.Element, namespaces: dict[str, str]
) -> Optional[TransXChangeLineDescription]:
    description_text_node = description_node.find("Description", namespaces)
    if description_text_node is None:
        return None
    description_text = description_text_node.text or ""
    description_vias_node = description_node.find("Vias", namespaces)
    description_vias: list[str] = []
    if description_vias_node is not None:
        for description_via in description_vias_node.findall("Via", namespaces):
            if description_via.text is not None:
                description_vias.append(
                    string.capwords(description_via.text.replace(" to ", " - "))
                )
    return TransXChangeLineDescription(
        string.capwords(description_text), description_vias
    )


def get_line_from_line_node(
    noc: str, line_node: ET.Element, namespaces: dict[str, str]
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
    return TransXChangeLine(
        line_name, line_id, noc, outbound_desc, inbound_desc
    )


def get_lines_from_service_node(
    noc: str, service_node: ET.Element, namespaces: dict[str, str]
) -> list[TransXChangeLine]:
    lines_node = service_node.find("Lines", namespaces)
    if lines_node is None:
        return []
    lines: list[TransXChangeLine] = []
    for line_node in lines_node.findall("Line", namespaces):
        line = get_line_from_line_node(noc, line_node, namespaces)
        if line is not None:
            lines.append(line)
    return lines


def get_services_from_transxchange_node(
    noc: str, transxchange_node: ET.Element, namespaces: dict[str, str]
) -> list[TransXChangeLine]:
    services_node = transxchange_node.find("Services", namespaces)
    if services_node is None:
        return []
    service_nodes = services_node.findall("Service", namespaces)
    services: list[TransXChangeLine] = []
    for service_node in service_nodes:
        lines = get_lines_from_service_node(noc, service_node, namespaces)
        services = services + lines
    return services


def get_noc_from_transxchange_node(
    transxchange_node: ET.Element, namespaces: dict[str, str]
) -> Optional[str]:
    operators_node = transxchange_node.find("Operators", namespaces)
    if operators_node is None:
        return None
    operator_node = operators_node.find("Operator", namespaces)
    if operator_node is None:
        return None
    national_operator_code = operator_node.find(
        "NationalOperatorCode", namespaces
    )
    if national_operator_code is None or national_operator_code.text is None:
        return None
    return national_operator_code.text


def get_lines_from_transxchange_node(
    transxchange_node: ET.Element,
    namespaces: dict[str, str],
    operator_nocs: set[str],
) -> Optional[list[TransXChangeLine]]:
    noc = get_noc_from_transxchange_node(transxchange_node, namespaces)
    if noc is None or noc not in operator_nocs:
        return None
    lines = get_services_from_transxchange_node(
        noc, transxchange_node, namespaces
    )
    return lines


def get_transxchange_namespaces(root: ET.Element) -> dict[str, str]:
    namespace_match = re.match(xmlns_re, root.tag)
    if namespace_match is None:
        namespace = ""
    else:
        namespace = namespace_match.group(1)
    return {"": namespace}


DbBusServiceInData = tuple[str, str, str, Optional[str], Optional[str]]
DbBusServiceViaInData = tuple[str, bool, str, int]


def insert_services(
    conn: Connection,
    services: list[TransXChangeLine],
) -> None:
    service_values: list[DbBusServiceInData] = []
    via_values: list[DbBusServiceViaInData] = []
    for service in services:
        service_values.append(
            (
                service.name,
                service.id,
                service.noc,
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
        if service.outbound_desc is not None:
            for i, via in enumerate(service.outbound_desc.vias):
                via_values.append(
                    (
                        service.id,
                        True,
                        via,
                        i,
                    )
                )
        if service.inbound_desc is not None:
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
            %s::BusServiceInData[],
            %s::BusServiceViaInData[]
        )""",
        [service_values, via_values],
    )
    conn.commit()


def extract_data_from_bods_xml(
    xml: str, operator_nocs: set[str]
) -> Optional[list[TransXChangeLine]]:
    root = ET.fromstring(xml)
    namespaces = get_transxchange_namespaces(root)
    return get_lines_from_transxchange_node(root, namespaces, operator_nocs)


def extract_data_from_bods_zipfile(
    zip: zipfile.ZipFile, operator_nocs: set[str]
) -> list[TransXChangeLine]:
    data: list[TransXChangeLine] = []
    for file_name in zip.namelist():
        file_path = zipfile.Path(zip, file_name)
        file_extension = file_path.suffix
        if file_extension == ".zip":
            with zip.open(file_name) as child_zip:
                child_filedata = io.BytesIO(child_zip.read())
                with zipfile.ZipFile(child_filedata) as child_zipfile:
                    child_data = extract_data_from_bods_zipfile(
                        child_zipfile, operator_nocs
                    )
                    data = data + child_data
        elif file_extension == ".xml":
            information(f"Reading service file {file_name}")
            xml = file_path.read_text()
            file_data = extract_data_from_bods_xml(xml, operator_nocs)
            if file_data is not None:
                data = data + file_data
    return data


def extract_data_from_bods_zip(
    zip_path: str | Path, operator_nocs: set[str]
) -> list[TransXChangeLine]:
    with zipfile.ZipFile(zip_path) as zip:
        return extract_data_from_bods_zipfile(zip, operator_nocs)


def populate_bus_services(
    conn: Connection, operator_nocs: set[str], bods_path: str
) -> None:
    information("Retrieving bus services")
    data = extract_data_from_bods_zip(bods_path, operator_nocs)
    information("Inserting bus services")
    insert_services(conn, data)
