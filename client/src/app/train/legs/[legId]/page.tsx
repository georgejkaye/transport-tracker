"use client"

import bbox from "@turf/bbox"
import Link from "next/link"
import { Dispatch, SetStateAction, useMemo, useState, use } from "react"
import {
  Layer,
  LineLayer,
  LngLatBoundsLike,
  Map,
  Source,
  ViewState,
  Marker,
  FullscreenControl,
  NavigationControl,
  ScaleControl,
  Popup,
} from "react-map-gl/maplibre"
import { FeatureCollection, Position } from "geojson"

import {
  dateToTimeString,
  getDurationString,
  getLegColour,
  getLegOperator,
  getMilesAndChainsString,
  getTrainServiceString,
  maybeDateToTimeString,
  maybeDateToTimeStringFromString,
  TrainLeg,
  TrainLegCall,
  TrainLegSegment,
  TrainService,
  TrainStockReport,
} from "@/app/structs"
import {
  Delay,
  getDelayOrUndefined,
  getDelayOrUndefinedString,
  getDelayStyle,
  PlanActTime,
  ShortStationLink,
} from "@/app/leg"
import { Line } from "@/app/line"
import { Loader } from "@/app/loader"
import { linkStyle } from "@/app/styles"
import { isNumber } from "@/app/utils/number"
import client from "@/app/api/client"
import { getLongDate } from "@/app/utils/datetime"
import {
  TrainLegCallOutData,
  TrainLegOutData,
  TrainLegServiceOutData,
  TrainLegStockSegmentOutData,
  TrainStockReportOutData,
} from "@/app/utils/train"
import { notFound, useRouter } from "next/navigation"
import {
  getBoundingBoxForFeatureCollection,
  getFeatureCollection,
} from "@/app/utils/map"

const getLineLayer = (leg: TrainLegOutData): LineLayer => ({
  id: "line",
  source: "geometry",
  type: "line",
  paint: {
    "line-width": 5,
    "line-color": getLegColour(),
  },
  layout: {
    "line-cap": "round",
  },
})

const getLineFeatureCollection = (geometry: Position[]): FeatureCollection => ({
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      geometry: {
        type: "LineString",
        coordinates: geometry,
      },
      properties: {},
    },
  ],
})

const gbMidpointLng = -2.547855
const gbMidpointLat = 54.00366
const boundingBoxPadding = 0.05

const Pin = (props: {
  size: number
  fillColour: string
  strokeColour: string
}) => (
  <svg height={props.size} viewBox="0 0 48 48" style={{ cursor: "pointer" }}>
    <circle
      cx="24"
      cy="24"
      r="18"
      style={{
        fill: props.fillColour,
        stroke: props.strokeColour,
        strokeWidth: 7,
      }}
    />
  </svg>
)

const LegCallMarker = (props: {
  leg: TrainLegOutData
  call: TrainLegCallOutData
  setCurrentLegCall: Dispatch<SetStateAction<TrainLegCallOutData | undefined>>
}) => {
  let { leg, call, setCurrentLegCall } = props
  let { delay, text } =
    call.plan_dep && call.act_dep
      ? getDelayOrUndefinedString(call.plan_dep, call.act_dep)
      : call.plan_arr && call.act_arr
        ? getDelayOrUndefinedString(call.plan_arr, call.act_arr)
        : {
            delay: 0,
            text: "",
          }
  const onClickMarker = (e: React.MouseEvent<HTMLDivElement>) => {
    e.stopPropagation()
    setCurrentLegCall(call)
  }
  const onMouseEnterMarker = (e: React.MouseEvent<HTMLDivElement>) => {
    e.stopPropagation()
    setCurrentLegCall(call)
  }
  const onMouseLeaveMarker = (e: React.MouseEvent<HTMLDivElement>) => {
    e.stopPropagation()
  }
  return !call ? (
    ""
  ) : (
    <Marker longitude={0} latitude={0} anchor="center">
      <div onMouseEnter={onMouseEnterMarker} onClick={onClickMarker}>
        <Pin
          size={28}
          fillColour={getDelayStyle(delay)}
          strokeColour={getLegColour()}
        />
      </div>
    </Marker>
  )
}

const LegCallPopup = (props: {
  currentLegCall: TrainLegCallOutData
  stationPoint: [number, number]
  setCurrentLegCall: Dispatch<SetStateAction<TrainLegCallOutData | undefined>>
}) => {
  let { currentLegCall, stationPoint, setCurrentLegCall } = props
  return (
    <Popup
      anchor="bottom"
      longitude={stationPoint[0]}
      latitude={stationPoint[1]}
      onClose={() => setCurrentLegCall(undefined)}
      closeButton={false}
      offset={15}
      maxWidth="60"
    >
      <div className="flex flex-col px-1 gap-2">
        <div>
          <div>
            <b className={`text-lg mb-2 ${linkStyle}`}>
              <Link
                href={`/train/stations/${currentLegCall.station.station_crs}`}
              >
                {currentLegCall.station.station_name} [
                {currentLegCall.station.station_crs}]
              </Link>
            </b>
          </div>
          {currentLegCall.platform && (
            <div>platform {currentLegCall.platform}</div>
          )}
        </div>
        {(currentLegCall.plan_arr || currentLegCall.act_arr) && (
          <div className="flex flex-row gap-2">
            <div className="w-5 text-left mr-2">arr</div>
            <div>
              {currentLegCall.plan_arr
                ? maybeDateToTimeStringFromString(currentLegCall.plan_arr)
                : ""}
            </div>
            <div>
              <b>
                {currentLegCall.act_arr
                  ? maybeDateToTimeStringFromString(currentLegCall.act_arr)
                  : ""}
              </b>
            </div>
            <Delay
              plan={
                !currentLegCall.plan_arr
                  ? null
                  : new Date(Date.parse(currentLegCall.plan_arr))
              }
              act={
                !currentLegCall.act_arr
                  ? null
                  : new Date(Date.parse(currentLegCall.act_arr))
              }
            />
          </div>
        )}
        {(currentLegCall.plan_dep || currentLegCall.act_dep) && (
          <div className="flex flex-row gap-2">
            <div className="w-5 text-left mr-2">dep</div>
            <div>
              {currentLegCall.plan_dep
                ? maybeDateToTimeStringFromString(currentLegCall.plan_dep)
                : ""}
            </div>
            <div>
              <b>
                {currentLegCall.act_dep
                  ? maybeDateToTimeStringFromString(currentLegCall.act_dep)
                  : ""}
              </b>
            </div>
            <Delay
              plan={
                !currentLegCall.plan_dep
                  ? null
                  : new Date(Date.parse(currentLegCall.plan_dep))
              }
              act={
                !currentLegCall.act_dep
                  ? null
                  : new Date(Date.parse(currentLegCall.act_dep))
              }
            />
          </div>
        )}
      </div>
    </Popup>
  )
}

const TrainLegMap = (props: { leg: TrainLegOutData }) => {
  let { leg } = props
  const [currentStation, setCurrentStation] = useState<
    TrainLegCallOutData | undefined
  >(undefined)
  let {
    data: geometries,
    isLoading,
    error,
  } = client.useQuery("get", "/train/legs/geometries/{leg_id}", {
    params: {
      path: {
        leg_id: leg.leg_id,
      },
    },
  })
  let featureCollection = getFeatureCollection(
    geometries?.geometry ?? [],
    "#000000",
  )
  let bounds = featureCollection
    ? getBoundingBoxForFeatureCollection(featureCollection)
    : undefined
  let layerStyle = getLineLayer(leg)
  let initialViewState: Partial<ViewState> & { bounds?: LngLatBoundsLike } =
    !geometries
      ? {
          longitude: gbMidpointLng,
          latitude: gbMidpointLat,
          zoom: 8,
        }
      : {
          bounds: [
            bounds?.minLng ?? 0 - boundingBoxPadding,
            bounds?.minLat ?? 0 - boundingBoxPadding,
            bounds?.maxLng ?? 0 + boundingBoxPadding,
            bounds?.maxLat ?? 0 + boundingBoxPadding,
          ],
        }
  let markers = useMemo(
    () =>
      leg.calls.map((call, i) => (
        <LegCallMarker
          key={i}
          leg={leg}
          call={call}
          setCurrentLegCall={setCurrentStation}
        />
      )),
    [],
  )
  return (
    <div className="overflow-hidden">
      <Map
        initialViewState={initialViewState}
        style={{ height: 800 }}
        mapStyle={`https://api.maptiler.com/maps/streets-v2/style.json?key=${process.env.NEXT_PUBLIC_MAPTILER_KEY}`}
      >
        <FullscreenControl position="top-left" />
        <NavigationControl position="top-left" />
        <ScaleControl />
        {!geometries ? (
          ""
        ) : (
          <Source id="geometry" type="geojson" data={geometries}>
            <Layer {...layerStyle} />
          </Source>
        )}
        {markers}
        {currentStation && (
          <LegCallPopup
            currentLegCall={currentStation}
            stationPoint={[0, 0]}
            setCurrentLegCall={setCurrentStation}
          />
        )}
      </Map>
    </div>
  )
}

const TrainLegService = (props: { service: TrainLegServiceOutData }) => {
  let { service } = props
  return (
    <div>
      <div>{getTrainServiceString(service)}</div>
    </div>
  )
}

const TrainLegServices = (props: { services: TrainLegServiceOutData[] }) => {
  let { services } = props
  return (
    <div className="flex-1">
      <div className="font-bold text-xl mb-2">Services</div>
      <div className="flex flex-row">
        {services.map((service) => (
          <TrainLegService key={service.service_id} service={service} />
        ))}
      </div>
    </div>
  )
}

const LegCallRow = (props: { call: TrainLegCallOutData }) => {
  let { call } = props
  let platformString = !call.platform ? "-" : call.platform
  return (
    <div className="flex flex-row gap-2 items-center">
      <div className="w-14 hidden md:block">{call.station.station_crs}</div>
      <ShortStationLink station={call.station} />
      <div className="w-6 text-center">{platformString}</div>
      <div className="flex flex-col md:flex-row">
        <PlanActTime
          act={!call.act_arr ? null : new Date(Date.parse(call.act_arr))}
          plan={!call.plan_arr ? null : new Date(Date.parse(call.plan_arr))}
        />
        <PlanActTime
          act={!call.act_dep ? null : new Date(Date.parse(call.act_dep))}
          plan={!call.plan_dep ? null : new Date(Date.parse(call.plan_dep))}
        />
      </div>
    </div>
  )
}

const TrainLegStats = (props: { leg: TrainLegOutData }) => {
  let { leg } = props
  return (
    <div className="flex flex-row gap-2">
      {/* <div>
        {!leg.distance ? (
          ""
        ) : (
          <div>{getMilesAndChainsString(leg.distance)}</div>
        )}
      </div>
      <div>•</div>
      <div>
        {!leg.duration ? "" : <div>{getDurationString(leg.duration)}</div>}
      </div> */}
    </div>
  )
}

const TrainLegCalls = (props: { calls: TrainLegCallOutData[] }) => {
  let { calls } = props
  return (
    <div>
      <h2 className="text-xl font-bold pb-2">Calls</h2>
      <div className="flex flex-col gap-2">
        {calls.map((call, i) => {
          return (
            <div className="flex flex-col gap-2" key={i}>
              <Line />
              <LegCallRow call={call} />
            </div>
          )
        })}
      </div>
    </div>
  )
}

const TrainStockReportLine = (props: { stock: TrainStockReportOutData }) => {
  let { stock } = props
  let stockDescription = !stock.stock_class ? (
    ""
  ) : (
    <Link href={`/train/stock/${stock.stock_class}`}>
      {`Class ${stock.stock_class}${
        !stock.stock_subclass ? "" : `/${stock.stock_subclass}`
      }`}
    </Link>
  )
  let stockNumber = !stock.stock_class ? (
    ""
  ) : (
    <Link href={`/train/stock/unit/${stock.stock_class}`}>
      {stock.stock_number}
    </Link>
  )
  let stockDescriptionElements = stock.stock_number ? (
    <div className="flex flex-row gap-2">
      {stockNumber}
      {!stock.stock_class ? "" : stockDescription}
    </div>
  ) : (
    stockDescription
  )
  let stockCarsText = !stock.stock_cars ? "" : `${stock.stock_cars} cars`
  return (
    <li className="flex flex-row gap-2">
      <div className="">{stockDescriptionElements}</div>
      {stockCarsText === "" ? (
        ""
      ) : (
        <div className="px-1 border">{stockCarsText}</div>
      )}
    </li>
  )
}

const TrainLegStockSegment = (props: {
  isOnlySegment: boolean
  segment: TrainLegStockSegmentOutData
}) => {
  let { isOnlySegment, segment } = props
  return (
    <div>
      {!isOnlySegment && (
        <h3 className="font-bold text-lg pb-2">
          {segment.stock_start.station_name} to {segment.stock_end.station_name}
        </h3>
      )}
      <ul className="flex flex-col gap-2 list-disc">
        {segment.stock_reports.map((stock, i) => (
          <TrainStockReportLine key={i} stock={stock} />
        ))}
      </ul>
    </div>
  )
}

const TrainLegStockSegments = (props: {
  segments: TrainLegStockSegmentOutData[]
}) => {
  let { segments } = props
  return (
    <div className="flex-1">
      <h2 className="font-bold text-xl pb-2">Rolling stock</h2>
      <div className="flex flex-col gap-4">
        {segments.map((segment, i) => (
          <TrainLegStockSegment
            isOnlySegment={segments.length == 1}
            segment={segment}
            key={i}
          />
        ))}
      </div>
    </div>
  )
}

interface ContentProps {
  legId: number
}

const Content = ({ legId }: ContentProps) => {
  let router = useRouter()
  const {
    data: leg,
    error,
    isLoading,
  } = client.useQuery("get", "/train/legs/{leg_id}", {
    params: { path: { leg_id: legId } },
  })
  return !leg ? (
    <Loader />
  ) : (
    <div className="flex flex-col gap-4 mx-4 my-2">
      <h1 className="text-3xl font-bold">
        {`${leg.calls[0]?.station.station_name} to ${
          leg.calls[leg?.calls.length - 1]?.station.station_name
        }`}
      </h1>
      <div className="flex flex-col lg:flex-row gap-2 items-baseline">
        <div className="text-xl">
          {getLongDate(leg.calls[0]?.plan_dep + "")}
        </div>
        <div>operated by {getLegOperator(leg)}</div>
      </div>
      <TrainLegMap leg={leg} />
      <Line />
      <TrainLegStats leg={leg} />
      <Line />
      <div className="flex flex-col lg:flex-row gap-4">
        <TrainLegServices services={leg?.services} />
        <div className="lg:hidden">
          <Line />
        </div>
        <TrainLegStockSegments segments={leg?.stock} />
      </div>
      <Line />
      <TrainLegCalls calls={leg?.calls} />
    </div>
  )
}

const Page = (props: {
  params: Promise<{ userId: string; legId: string }>
}) => {
  let { legId } = use(props.params)
  return !isNumber(legId) ? notFound() : <Content legId={Number(legId)} />
}

export default Page
