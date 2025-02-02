"use client"

import { getTrainLeg } from "@/app/data"
import bbox from "@turf/bbox"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Dispatch, SetStateAction, useEffect, useMemo, useState } from "react"
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
  dateToLongString,
  dateToTimeString,
  getDurationString,
  getLegColour,
  getMilesAndChainsString,
  getTrainServiceString,
  TrainLeg,
  TrainLegCall,
  TrainLegSegment,
  TrainService,
  TrainStockReport,
} from "@/app/structs"
import {
  Delay,
  getDelayOrUndefined,
  getDelayStyle,
  PlanActTime,
  ShortStationLink,
} from "@/app/leg"
import { Line } from "@/app/line"
import { Loader } from "@/app/loader"

const getLineLayer = (leg: TrainLeg): LineLayer => ({
  id: "line",
  source: "geometry",
  type: "line",
  paint: {
    "line-width": 5,
    "line-color": getLegColour(leg),
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

const getLineAndBoundingBox = (leg: TrainLeg) => {
  if (!leg.geometry) {
    return undefined
  }
  let line = getLineFeatureCollection(leg.geometry)
  let [minLng, minLat, maxLng, maxLat] = bbox(line)
  return {
    line,
    minLng,
    minLat,
    maxLng,
    maxLat,
  }
}

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
  leg: TrainLeg
  call: TrainLegCall
  setCurrentLegCall: Dispatch<SetStateAction<TrainLegCall | undefined>>
}) => {
  let { leg, call, setCurrentLegCall } = props
  let { delay, text } =
    call.planDep && call.actDep
      ? getDelayOrUndefined(call.planDep, call.actDep)
      : call.planArr && call.actArr
      ? getDelayOrUndefined(call.planArr, call.actArr)
      : {
          delay: 0,
          text: "",
        }
  const onClickMarker = (e: React.MouseEvent<HTMLDivElement>) => {
    e.stopPropagation()
    setCurrentLegCall(call)
  }
  return !call.point ? (
    ""
  ) : (
    <Marker longitude={call.point[0]} latitude={call.point[1]} anchor="center">
      <div onClick={onClickMarker}>
        <Pin
          size={28}
          fillColour={getDelayStyle(delay)}
          strokeColour={getLegColour(leg)}
        />
      </div>
    </Marker>
  )
}

const LegCallPopup = (props: {
  currentStation: TrainLegCall
  stationPoint: [number, number]
  setCurrentLegCall: Dispatch<SetStateAction<TrainLegCall | undefined>>
}) => {
  let { currentStation, stationPoint, setCurrentLegCall } = props
  return (
    <Popup
      anchor="top"
      longitude={stationPoint[0]}
      latitude={stationPoint[1]}
      onClose={() => setCurrentLegCall(undefined)}
      closeButton={false}
    >
      <div className="flex flex-col p-1 gap-2">
        <div>
          <b className="text-lg mb-2">
            {currentStation.station.name} [{currentStation.station.crs}]
          </b>
        </div>
        <div className="flex flex-row gap-2">
          <div className="w-5 text-left mr-2">arr</div>
          <div>
            {currentStation.planArr
              ? dateToTimeString(currentStation.planArr)
              : ""}
          </div>
          <div>
            <b>
              {currentStation.actArr
                ? dateToTimeString(currentStation.actArr)
                : ""}
            </b>
          </div>
          <Delay plan={currentStation.planArr} act={currentStation.actArr} />
        </div>
        <div className="flex flex-row gap-2">
          <div className="w-5 text-left mr-2">dep</div>
          <div>
            {currentStation.planDep
              ? dateToTimeString(currentStation.planDep)
              : ""}
          </div>
          <div>
            <b>
              {currentStation.actDep
                ? dateToTimeString(currentStation.actDep)
                : ""}
            </b>
          </div>
          <Delay plan={currentStation.planDep} act={currentStation.actDep} />
        </div>
      </div>
    </Popup>
  )
}

const TrainLegMap = (props: { leg: TrainLeg }) => {
  let { leg } = props
  const [currentStation, setCurrentStation] = useState<
    TrainLegCall | undefined
  >(undefined)
  let data = getLineAndBoundingBox(leg)
  let layerStyle = getLineLayer(leg)
  let initialViewState: Partial<ViewState> & { bounds?: LngLatBoundsLike } =
    !data
      ? {
          longitude: gbMidpointLng,
          latitude: gbMidpointLat,
          zoom: 8,
        }
      : {
          bounds: [
            data.minLng - boundingBoxPadding,
            data.minLat - boundingBoxPadding,
            data.maxLng + boundingBoxPadding,
            data.maxLat + boundingBoxPadding,
          ],
        }
  let markers = useMemo(
    () =>
      leg.calls.map((call) => (
        <LegCallMarker
          leg={leg}
          call={call}
          setCurrentLegCall={setCurrentStation}
        />
      )),
    []
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
        {!data ? (
          ""
        ) : (
          <Source id="geometry" type="geojson" data={data.line}>
            <Layer {...layerStyle} />
          </Source>
        )}
        {markers}
        {currentStation && currentStation.point && (
          <LegCallPopup
            currentStation={currentStation}
            stationPoint={currentStation.point}
            setCurrentLegCall={setCurrentStation}
          />
        )}
      </Map>
    </div>
  )
}

const TrainLegService = (props: { service: TrainService }) => {
  let { service } = props
  return (
    <div>
      <div>{getTrainServiceString(service)}</div>
    </div>
  )
}

const TrainLegServices = (props: { services: TrainService[] }) => {
  let { services } = props
  return (
    <div>
      <h2 className="font-bold text-lg mb-2">Services</h2>
      <div className="flex flex-row">
        {services.map((service, i) => (
          <TrainLegService key={i} service={service} />
        ))}
      </div>
    </div>
  )
}

const LegCallRow = (props: { call: TrainLegCall }) => {
  let { call } = props
  let platformString = !call.platform ? "-" : call.platform
  return (
    <div className="flex flex-row gap-2 items-center">
      <div className="w-14 hidden md:block">{call.station.crs}</div>
      <ShortStationLink station={call.station} />
      <div className="w-6 text-center">{platformString}</div>
      <div className="flex flex-col md:flex-row">
        <PlanActTime plan={call.planArr} act={call.actArr} />
        <PlanActTime plan={call.planDep} act={call.actDep} />
      </div>
    </div>
  )
}

const TrainLegStats = (props: { leg: TrainLeg }) => {
  let { leg } = props
  return (
    <div className="flex flex-row gap-2">
      <div>
        {!leg.distance ? (
          ""
        ) : (
          <div>{getMilesAndChainsString(leg.distance)}</div>
        )}
      </div>
      <div>•</div>
      <div>
        {!leg.duration ? "" : <div>{getDurationString(leg.duration)}</div>}
      </div>
    </div>
  )
}

const TrainLegCalls = (props: { calls: TrainLegCall[] }) => {
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

const TrainStockReportLine = (props: { stock: TrainStockReport }) => {
  let { stock } = props
  let stockDescription = !stock.classNo ? (
    ""
  ) : (
    <Link href={`/train/stock/${stock.classNo}`}>
      {`Class ${stock.classNo}${
        !stock.subclassNo ? "" : `/${stock.subclassNo}`
      }`}
    </Link>
  )
  let stockNumber = !stock.stockNo ? (
    ""
  ) : (
    <Link href={`/train/stock/unit/${stock.stockNo}`}>{stock.stockNo}</Link>
  )
  let stockDescriptionElements = stock.stockNo ? (
    <div className="flex flex-row gap-2">
      {stockNumber}
      {!stock.classNo ? "" : stockDescription}
    </div>
  ) : (
    stockDescription
  )
  let stockCarsText = !stock.cars ? "" : `${stock.cars} cars`
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

const TrainLegStockSegment = (props: { segment: TrainLegSegment }) => {
  let { segment } = props
  return (
    <div>
      <h3 className="font-bold text-lg pb-2">
        {segment.start.name} to {segment.end.name}
      </h3>
      <ul className="flex flex-col gap-2 list-disc">
        {segment.stocks.map((stock, i) => (
          <TrainStockReportLine key={i} stock={stock} />
        ))}
      </ul>
    </div>
  )
}

const TrainLegStockSegments = (props: { segments: TrainLegSegment[] }) => {
  let { segments } = props
  return (
    <div>
      <h2 className="font-bold text-xl pb-2">Rolling stock</h2>
      <div className="flex flex-col gap-4">
        {segments.map((segment, i) => (
          <TrainLegStockSegment segment={segment} key={i} />
        ))}
      </div>
    </div>
  )
}

const Page = ({ params }: { params: { legId: string } }) => {
  let { legId } = params
  let router = useRouter()
  let [leg, setLeg] = useState<TrainLeg | undefined>(undefined)
  useEffect(() => {
    let legIdNumber = parseInt(legId)
    if (isNaN(legIdNumber)) {
      router.push("/")
    } else {
      const getLegData = async () => {
        let legData = await getTrainLeg(legIdNumber)
        if (!legData) {
          router.push("/")
        } else {
          setLeg(legData)
        }
      }
      getLegData()
    }
  }, [])
  return !leg ? (
    <Loader />
  ) : (
    <div className="flex flex-col gap-4 mx-4">
      <h1 className="text-2xl font-bold">
        {`${leg.calls[0].station.name} to ${
          leg.calls[leg.calls.length - 1].station.name
        }`}
      </h1>
      <div className="text-xl">{dateToLongString(leg.start)}</div>
      <TrainLegMap leg={leg} />
      <Line />
      <TrainLegStats leg={leg} />
      <Line />
      <TrainLegServices services={leg.services} />
      <Line />
      <TrainLegStockSegments segments={leg.stock} />
      <Line />
      <TrainLegCalls calls={leg.calls} />
    </div>
  )
}

export default Page
