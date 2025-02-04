import { LegIconLink, EndpointSection, TotalStat } from "@/app/leg"
import {
  TrainLeg,
  getMilesAndChainsString,
  getLegOrigin,
  getLegDestination,
  dateToShortString,
  getMaybeDurationString,
  getDurationString,
  getLegColour,
  Stats,
  StationStat,
} from "@/app/structs"
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
import { Feature, FeatureCollection, Position } from "geojson"
import bbox from "@turf/bbox"

const LegRow = (props: { leg: TrainLeg }) => {
  let { leg } = props
  let mileString = !leg.distance ? "" : getMilesAndChainsString(leg.distance)
  let origin = getLegOrigin(leg)
  let destination = getLegDestination(leg)
  return (
    <div className="flex flex-row gap-4 justify-center">
      <div className="flex flex-col lg:flex-row gap-4">
        <div className="flex flex-row gap-2 lg:w-80 items-center">
          <LegIconLink id={leg.id} />
          <div className="text-xs lg:hidden">•</div>
          <div className="lg:px-2">{dateToShortString(leg.start)}</div>
          <div className="text-xs lg:hidden">•</div>
          <div className="lg:w-28">{getMaybeDurationString(leg.duration)}</div>
          <div className="text-xs lg:hidden">•</div>
          <div className="lg:w-32">{mileString}</div>
        </div>
        <div className="flex flex-col md:flex-row gap-2">
          <div className="flex flex-row gap-2 items-center">
            <div className="text-right w-10 text-xs lg:hidden">from</div>
            <EndpointSection call={origin} origin={true} />
          </div>
          <div className="flex flex-row gap-2 items-center">
            <div className="text-right w-10 text-xs lg:hidden">to</div>
            <EndpointSection call={destination} origin={false} />
          </div>
        </div>
      </div>
    </div>
  )
}

const getLinesAndBoundingBox = (legs: TrainLeg[]) => {
  let features: Feature[] = []
  for (const leg of legs) {
    if (leg.geometry) {
      features.push({
        type: "Feature",
        geometry: { type: "LineString", coordinates: leg.geometry },
        properties: { color: getLegColour(leg), width: 5 },
      })
    }
  }
  let featureCollection: FeatureCollection = {
    type: "FeatureCollection",
    features,
  }
  let [minLng, minLat, maxLng, maxLat] = bbox(featureCollection)
  return { featureCollection, minLng, minLat, maxLng, maxLat }
}

const getLineLayer = (): LineLayer => ({
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
})

const boundingBoxPadding = 0.05

export const LegMap = (props: { legs: TrainLeg[] }) => {
  let { legs } = props
  let data = getLinesAndBoundingBox(legs)
  let initialViewState: Partial<ViewState> & { bounds?: LngLatBoundsLike } = {
    bounds: [
      data.minLng - boundingBoxPadding,
      data.minLat - boundingBoxPadding,
      data.maxLng + boundingBoxPadding,
      data.maxLat + boundingBoxPadding,
    ],
  }
  let layerStyle = getLineLayer()
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
        <Source id="lines" type="geojson" data={data.featureCollection}>
          <Layer {...layerStyle} />
        </Source>
      </Map>
    </div>
  )
}

export const GeneralStats = (props: { stats: Stats }) => {
  let { stats } = props
  return (
    <div className="flex flex-row flex-wrap gap-4 py-2">
      <TotalStat title="Legs" value={`${stats.legStats.length}`} />
      <TotalStat
        title="Distance"
        value={getMilesAndChainsString(stats.distance)}
      />
      <TotalStat title="Duration" value={getDurationString(stats.duration)} />
    </div>
  )
}

export const StationStats = (props: { stats: StationStat[] }) => {
  let { stats } = props
  return (
    <div className="flex rounded flex-col border-2 border-red-400 pb-2">
      <div className="bg-red-500 p-2 font-bold text-white">Stations</div>
      <div className="flex flex-row p-2 gap-2 px-4">
        <div className="font-bold w-10">Rank</div>
        <div className="font-bold w-96">Station</div>
        <div className="font-bold w-72">Operator</div>
        <div className="font-bold w-14">Boards</div>
        <div className="font-bold w-14">Alights</div>
        <div className="font-bold w-14">Calls</div>
        <div className="font-bold w-14">Total</div>
      </div>
      {stats.map((station, i) => (
        <div
          className={`p-2 flex flex-row gap-2 px-4 ${
            i > 0 ? "border-t-2" : ""
          }`}
        >
          <div className="w-10">{i + 1}</div>
          <div className="w-96 flex flex-row">
            <div className="w-12">{station.crs}</div>
            <div>{station.name}</div>
          </div>
          <div className="w-72">{station.operatorName}</div>
          <div className="w-14">{station.boards}</div>
          <div className="w-14">{station.alights}</div>
          <div className="w-14">{station.intermediates}</div>
          <div className="w-14">
            {station.boards + station.alights + station.intermediates}
          </div>
        </div>
      ))}
    </div>
  )
}

export const LegList = (props: { legs: TrainLeg[] }) =>
  props.legs.map((leg, i) => (
    <div className="flex flex-col gap-2" key={i}>
      <hr className="h-px border-0 bg-gray-600" />
      <LegRow key={leg.id} leg={leg} />
    </div>
  ))
