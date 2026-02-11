import client from "@/app/api/client"

import {
  AttributionControl,
  Layer,
  LineLayer,
  Map,
  Source,
} from "react-map-gl/maplibre"
import { getLongDateAndTime } from "@/app/utils/datetime"
import { getDelayString } from "@/app/utils/delay"
import { getMilesAndChainsStringFromNumber } from "@/app/utils/distance"
import { getDurationStringFromString } from "@/app/utils/duration"
import { TransportUserTrainLegOutData } from "@/app/utils/train"
import { FaTrain } from "react-icons/fa6"
import {
  getBoundingBoxForFeatureCollection,
  getFeatureCollection,
} from "@/app/utils/map"
import { Loader } from "@/app/loader"
import { Fragment } from "react"

interface LegFeedItemMapProps {
  leg: TransportUserTrainLegOutData
}

const lineLayer: LineLayer = {
  id: "line",
  source: "geometry",
  type: "line",
  paint: {
    "line-width": 5,
    "line-color": ["get", "color"],
  },
  layout: {
    "line-cap": "round",
  },
}

const boundingBoxPadding = 0.1

const LegFeedItemMap = ({ leg }: LegFeedItemMapProps) => {
  let { data, isLoading, error } = client.useQuery(
    "get",
    "/train/legs/geometries/{leg_id}",
    {
      params: {
        path: {
          leg_id: leg.leg_id,
        },
      },
    },
  )
  let featureCollection = data?.geometry
    ? getFeatureCollection(data?.geometry, "#0c0040")
    : undefined
  let bounds = featureCollection
    ? getBoundingBoxForFeatureCollection(featureCollection)
    : undefined

  let windowWidth = window.innerWidth
  let width = windowWidth < 1024 ? "calc(100vw - 60px)" : "1000"
  let viewState = bounds && {
    bounds: [
      bounds.minLng - boundingBoxPadding,
      bounds.minLat - boundingBoxPadding,
      bounds.maxLng + boundingBoxPadding,
      bounds.maxLat + boundingBoxPadding,
    ],
  }

  return isLoading ? (
    <Loader />
  ) : (
    <div className="overflow-hidden">
      {viewState && (
        <Map
          attributionControl={false}
          interactive={false}
          style={{ height: 400, width }}
          {...viewState}
          mapStyle={"https://tiles.openfreemap.org/styles/bright"}
        >
          <Source id="lines" type="geojson" data={featureCollection}>
            <Layer {...lineLayer} />
          </Source>
          <AttributionControl compact={true} />
        </Map>
      )}
    </div>
  )
}

interface LegFeedItemProps {
  leg: TransportUserTrainLegOutData
}

const LegFeedItem = ({ leg }: LegFeedItemProps) => {
  return (
    <div className="shadow-lg p-4 flex flex-col gap-2">
      <div className="text-sm text-gray-600">
        {getLongDateAndTime(leg.start_datetime)}
      </div>
      <div className="font-bold text-xl flex flex-row gap-2 items-center">
        <FaTrain />
        {leg.board_station.station_name} to {leg.alight_station.station_name}
      </div>
      <div className="flex flex-row gap-4">
        <div>{leg.operator.operator_code}</div>
        <div>
          {leg.distance &&
            getMilesAndChainsStringFromNumber(parseFloat(leg.distance))}
        </div>
        <div>{leg.duration && getDurationStringFromString(leg.duration)}</div>
        {leg.delay !== null && leg.delay !== 0 && (
          <div>{getDelayString(leg.delay)} </div>
        )}
      </div>
      <LegFeedItemMap leg={leg} />
    </div>
  )
}

interface LegFeedProps {
  userId: number
}

const LegFeed = ({ userId }: LegFeedProps) => {
  const { data, fetchNextPage, hasNextPage, isFetching } =
    client.useInfiniteQuery(
      "get",
      "/users/{user_id}/train/legs",
      {
        params: {
          path: {
            user_id: userId,
          },
        },
      },
      {
        pageParamName: "page_no",
        getNextPageParam: (lastPage) => `${lastPage.current_page + 1}`,
        initialPageParam: 0,
      },
    )
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        {data?.pages.map((page) => (
          <Fragment key={page.current_page}>
            {page.items.map((leg) => (
              <LegFeedItem leg={leg} key={leg.leg_id} />
            ))}
          </Fragment>
        ))}
      </div>
      {hasNextPage && (
        <button onClick={() => fetchNextPage()} disabled={isFetching}>
          {isFetching ? "Loading..." : "Load more"}
        </button>
      )}
    </div>
  )
}

export default LegFeed
