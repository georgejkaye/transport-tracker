import {
  Layer,
  LineLayer,
  LngLatBoundsLike,
  Map,
  Source,
  ViewState,
  FullscreenControl,
  NavigationControl,
  ScaleControl,
} from "react-map-gl/maplibre"
import { Feature, FeatureCollection } from "geojson"
import bbox from "@turf/bbox"

import { getLegColour, TrainLeg } from "@/app/structs"

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
