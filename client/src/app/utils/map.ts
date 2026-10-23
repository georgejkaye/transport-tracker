import bbox from "@turf/bbox"
import { Feature, FeatureCollection } from "geojson"

export const getFeatureCollection = (
  points: [string, string][],
  colour: string,
): FeatureCollection => {
  let features: Feature[] = []
  let coordinates = points.map((coords) => [
    Number(coords[0]),
    Number(coords[1]),
  ])
  features.push({
    type: "Feature",
    geometry: { type: "LineString", coordinates },
    properties: { color: colour, width: 5 },
  })
  return {
    type: "FeatureCollection",
    features,
  }
}

export const getBoundingBoxForFeatureCollection = (
  featureCollection: FeatureCollection,
) => {
  let [minLng, minLat, maxLng, maxLat] = bbox(featureCollection)
  return { minLng, minLat, maxLng, maxLat }
}
