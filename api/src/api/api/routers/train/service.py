from datetime import date

from fastapi import APIRouter, HTTPException

from api.api.lifespan import get_rtt_api_client
from api.data.train.api import RttApiManager
from api.data.train.clients.gbnr import (
    RttGbnrClient,
    RttGbnrServiceNotFoundError,
)
from api.train.service.graph.builder import get_service_graph
from api.train.service.graph.classes import ServiceGraphData
from api.train.service.graph.serialise import serialise_service_graph

router = APIRouter(prefix="/service", tags=["train/service"])
__all__ = ["router"]


@router.get(
    "/graph/{identity}/{departure_date}",
    summary="Get a train service call graph",
)
async def get_train_service_graph(
    identity: str, departure_date: date
) -> ServiceGraphData:
    rtt_api_manager = RttApiManager(get_rtt_api_client())
    rtt_gbnr_client = RttGbnrClient(rtt_api_manager.get_access_token().token)
    try:
        graph_root = get_service_graph(
            identity, departure_date, rtt_gbnr_client
        )
    except RttGbnrServiceNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    if graph_root is None:
        raise HTTPException(
            status_code=404,
            detail=f"No service graph found for service {identity} on {departure_date}",
        )
    return serialise_service_graph(graph_root)
