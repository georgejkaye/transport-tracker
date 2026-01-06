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

import { paths } from "@/app/api/api"

export type TrainLegGeometry =
  paths["/train/legs/geometries/{leg_id}"]["get"]["responses"][200]["content"]["application/json"]

const getLinesAndBoundingBox = (legs: TrainLegGeometry[]) => {
  let features: Feature[] = []
  for (const leg of legs) {
    if (!leg.geometry) {
      continue
    }
    let coordinates = leg.geometry.map((coords) => [
      Number(coords[0]),
      Number(coords[1]),
    ])
    features.push({
      type: "Feature",
      geometry: { type: "LineString", coordinates },
      properties: { color: "#ff00ff", width: 5 },
    })
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

export const LegMap = (props: { legs: TrainLegGeometry[] }) => {
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
    <div className="overflow-hidden rounded">
      <Map
        initialViewState={initialViewState}
        style={{ height: 800 }}
        mapStyle={"https://tiles.openfreemap.org/styles/bright"}
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
