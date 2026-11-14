from fastapi import APIRouter

from api.api.lifespan import OperatorBrandLookup, get_operator_brand_lookup

router = APIRouter(prefix="/operators", tags=["train/operators"])


@router.get("/lookup", summary="Get operator lookup")
async def get_operator_colours() -> OperatorBrandLookup:
    return get_operator_brand_lookup()
