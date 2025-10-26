from api.db.types.bus import BusServiceDetails


def short_string_of_bus_service(service: BusServiceDetails) -> str:
    description = service.description_outbound
    if description == "":
        description = service.description_inbound
    return f"{service.service_line} {description} ({service.bus_operator.operator_name})"
