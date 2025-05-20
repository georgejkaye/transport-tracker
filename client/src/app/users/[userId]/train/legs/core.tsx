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
import { Feature, FeatureCollection } from "geojson"
import bbox from "@turf/bbox"
import { Duration } from "js-joda"

const LegRow = (props: { userId: number; leg: TrainLeg }) => {
  let { userId, leg } = props
  let mileString = !leg.distance ? "" : getMilesAndChainsString(leg.distance)
  let origin = getLegOrigin(leg)
  let destination = getLegDestination(leg)
  return (
    <div className="flex flex-row gap-4 justify-center">
      <div className="flex flex-col lg:flex-row gap-4">
        <div className="flex flex-row gap-2 lg:w-80 items-center">
          <LegIconLink userId={userId} legId={leg.id} />
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
            <EndpointSection userId={userId} call={origin} origin={true} />
          </div>
          <div className="flex flex-row gap-2 items-center">
            <div className="text-right w-10 text-xs lg:hidden">to</div>
            <EndpointSection
              userId={userId}
              call={destination}
              origin={false}
            />
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

export const TotalLegStats = (props: { legs: TrainLeg[] }) => {
  let { legs } = props
  let { distance, duration } = legs.reduce(
    ({ distance, duration }, cur) => {
      let newDistance = !cur.distance ? 0 : cur.distance
      let newDuration = !cur.duration ? Duration.ZERO : cur.duration
      return {
        distance: distance + newDistance,
        duration: duration.plusDuration(newDuration),
      }
    },
    { distance: 0, duration: Duration.ZERO }
  )
  return (
    <div className="flex flex-row flex-wrap gap-4 justify-center">
      <TotalStat title="Legs" value={`${legs.length}`} />
      <TotalStat title="Distance" value={getMilesAndChainsString(distance)} />
      <TotalStat title="Duration" value={getDurationString(duration)} />
    </div>
  )
}

export const LegList = (props: { userId: number; legs: TrainLeg[] }) =>
  props.legs.map((leg, i) => (
    <div className="flex flex-col gap-2" key={i}>
      <hr className="h-px border-0 bg-gray-600" />
      <LegRow userId={props.userId} key={leg.id} leg={leg} />
    </div>
  ))
