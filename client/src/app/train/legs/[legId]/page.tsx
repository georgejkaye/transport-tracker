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

// https://github.com/visgl/react-maplibre/blob/1.0-release/examples/controls/src/pin.tsx
const ICON = `M20.2,15.7L20.2,15.7c1.1-1.6,1.8-3.6,1.8-5.7c0-5.6-4.5-10-10-10S2,4.5,2,10c0,2,0.6,3.9,1.6,5.4c0,0.1,0.1,0.2,0.2,0.3
  c0,0,0.1,0.1,0.1,0.2c0.2,0.3,0.4,0.6,0.7,0.9c2.6,3.1,7.4,7.6,7.4,7.6s4.8-4.5,7.4-7.5c0.2-0.3,0.5-0.6,0.7-0.9
  C20.1,15.8,20.2,15.8,20.2,15.7z`

const pinStyle = (colour: string) => ({
  cursor: "pointer",
  fill: colour,
  stroke: "none",
})

const Pin = (props: { size: number; colour: string }) => (
  <svg height={props.size} viewBox="0 0 24 24" style={pinStyle(props.colour)}>
    <path d={ICON} />
  </svg>
)

const LegCallMarker = (props: {
  call: TrainLegCall
  setStationPopUp: Dispatch<SetStateAction<TrainLegCall | undefined>>
}) => {
  let { call, setStationPopUp } = props
  let { delay, text } =
    call.planDep && call.actDep
      ? getDelayOrUndefined(call.planDep, call.actDep)
      : call.planArr && call.actArr
      ? getDelayOrUndefined(call.planArr, call.actArr)
      : {
          delay: 0,
          text: "",
        }
  return !call.point ? (
    ""
  ) : (
    <Marker longitude={call.point[0]} latitude={call.point[1]} anchor="bottom">
      <div
        onMouseEnter={() => setStationPopUp(call)}
        onMouseLeave={() => setStationPopUp(undefined)}
      >
        <Pin size={20} colour={getDelayStyle(delay)} />
      </div>
    </Marker>
  )
}

const TrainLegMap = (props: { leg: TrainLeg }) => {
  let { leg } = props
  const [stationPopUp, setStationPopUp] = useState<TrainLegCall | undefined>(
    undefined
  )
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
        <LegCallMarker call={call} setStationPopUp={setStationPopUp} />
      )),
    []
  )
  return (
    <div className="overflow-hidden">
      <Map
        initialViewState={initialViewState}
        style={{ height: 800 }}
        mapStyle="https://api.maptiler.com/maps/streets-v2/style.json?key=eGNO3STJJMAIGpREfPUF"
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
        {stationPopUp && stationPopUp.point && (
          <Popup
            anchor="top"
            longitude={stationPopUp.point[0]}
            latitude={stationPopUp.point[1]}
            onClose={() => setStationPopUp(undefined)}
          >
            <div className="flex flex-col p-1 gap-2">
              <div>
                <b>
                  {stationPopUp.station.name} [{stationPopUp.station.crs}]
                </b>
              </div>
              <div className="flex flex-row gap-2">
                <div>
                  {stationPopUp.planArr
                    ? dateToTimeString(stationPopUp.planArr)
                    : ""}
                </div>
                <div>
                  <b>
                    {stationPopUp.actArr
                      ? dateToTimeString(stationPopUp.actArr)
                      : ""}
                  </b>
                </div>
                <Delay plan={stationPopUp.planArr} act={stationPopUp.actArr} />
                <div>
                  {stationPopUp.planDep
                    ? dateToTimeString(stationPopUp.planDep)
                    : ""}
                </div>
                <div>
                  <b>
                    {stationPopUp.actDep
                      ? dateToTimeString(stationPopUp.actDep)
                      : ""}
                  </b>
                </div>
                <Delay plan={stationPopUp.planDep} act={stationPopUp.actDep} />
              </div>
            </div>
          </Popup>
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
