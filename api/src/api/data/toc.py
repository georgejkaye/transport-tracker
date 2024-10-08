from dataclasses import dataclass
from api.data.train import (
    generate_natrail_token,
    get_kb_url,
    get_natrail_token_headers,
)
from api.data.core import get_tag_text, make_get_request, prefix_namespace
from api.data.credentials import get_api_credentials
import xml.etree.ElementTree as ET
from api.data.database import connect, disconnect, insert
from api.data.schema import toc_table
from psycopg2._psycopg import connection, cursor


@dataclass
class Toc:
    name: str
    atoc: str


@dataclass
class TocWithBrand:
    name: str
    atoc: str
    brand: list[Toc]


kb_tocs_namespace = "http://nationalrail.co.uk/xml/toc"


def pull_tocs(natrail_token: str) -> list[Toc]:
    kb_tocs_url = get_kb_url("tocs")
    headers = get_natrail_token_headers(natrail_token)
    kb_tocs = make_get_request(kb_tocs_url, headers=headers).text
    kb_tocs_xml = ET.fromstring(kb_tocs)
    tocs = []
    for toc in kb_tocs_xml.findall(
        prefix_namespace(kb_tocs_namespace, "TrainOperatingCompany")
    ):
        toc_name = get_tag_text(toc, "Name", kb_tocs_namespace)
        toc_code = get_tag_text(toc, "AtocCode", kb_tocs_namespace)
        tocs.append(Toc(toc_name, toc_code))
    return tocs


def populate_toc_table(conn: connection, cur: cursor, tocs: list[Toc]):
    fields = ["operator_name", "operator_id"]
    values: list[list[str | None]] = list(map(lambda x: [x.name, x.atoc], tocs))
    insert(cur, toc_table, fields, values)
    conn.commit()


def populate_tocs(conn: connection, cur: cursor):
    natrail_credentials = get_api_credentials("NATRAIL")
    token = generate_natrail_token(natrail_credentials)
    tocs = pull_tocs(token)
    populate_toc_table(conn, cur, tocs)


def get_brands_or_empty(brands: list | None) -> list[Toc]:
    if brands is None:
        return []
    return [Toc(brand["brand_name"], brand["brand_id"]) for brand in brands]


def get_tocs(conn: connection, cur: cursor) -> list[TocWithBrand]:
    query = """
        SELECT operator_name, operator_id, brands.brands
        FROM operator
        LEFT JOIN (
            SELECT
                brand.parent_operator,
                json_agg(json_build_object('brand_name', brand.brand_name, 'brand_id', brand.brand_id))
            AS brands
            FROM brand
            GROUP BY brand.parent_operator
        ) brands
        ON brands.parent_operator = operator.operator_id
    """
    cur.execute(query)
    rows = cur.fetchall()
    tocs = [
        TocWithBrand(
            row[0],
            row[1],
            get_brands_or_empty(row[2]),
        )
        for row in rows
    ]
    return tocs


if __name__ == "__main__":
    (conn, cur) = connect()
    populate_tocs(conn, cur)
    disconnect(conn, cur)
