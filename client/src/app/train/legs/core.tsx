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
  getBoardsPlusAlights,
  StationStatSorter,
  sortBy,
  getSorter,
} from "@/app/structs"
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
import { useEffect, useState } from "react"
import { FaAngleUp, FaAngleDown } from "react-icons/fa6"

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

interface TableColumn<T> {
  style: string
  title: string
  getValue: (t: T) => JSX.Element | string | number
  getOrder: (t1: T, t2: T, natural: boolean) => number
  naturalOrderAscending: boolean
}

const SortableTable = <T,>(props: {
  title: string
  columns: TableColumn<T>[]
  values: T[]
  numberToShow: number
  getKey: (t: T) => string
  rankSort: (t1: T, t2: T, natural: boolean) => number
}) => {
  let { title, columns, values, numberToShow, getKey, rankSort } = props
  let [sortedValues, setSortedValues] = useState(
    values
      .toSorted((t1, t2) => rankSort(t1, t2, true))
      .map((val, i) => ({ originalRank: i, value: val }))
  )
  let [sortingColumn, setSortingColumn] = useState(-1)
  let [sortingNaturalOrder, setSortingNaturalOrder] = useState(true)
  let [extended, setExtended] = useState(false)

  useEffect(() => {
    setSortedValues((values) =>
      values.toSorted((t1, t2) =>
        sortingColumn == -1
          ? (t1.originalRank - t2.originalRank) * (sortingNaturalOrder ? 1 : -1)
          : columns[sortingColumn].getOrder(
              t1.value,
              t2.value,
              sortingNaturalOrder
            )
      )
    )
  }, [sortingColumn, sortingNaturalOrder])

  const onClickToggleExtended = (_e: React.MouseEvent<HTMLDivElement>) =>
    setExtended((prev) => !prev)

  const ColumnHeader = (props: {
    i: number
    title: string
    style: string
    naturalOrderAscending: boolean
  }) => {
    let { i, title, style, naturalOrderAscending } = props
    const onClickHeader = (_e: React.MouseEvent<HTMLDivElement>) => {
      if (sortingColumn == i) {
        setSortingNaturalOrder((prev) => !prev)
      } else {
        setSortingColumn(i)
        setSortingNaturalOrder(true)
      }
    }
    const SortingArrow = (props: { i: number }) =>
      sortingColumn == props.i &&
      (sortingNaturalOrder === naturalOrderAscending ? (
        <FaAngleUp />
      ) : (
        <FaAngleDown />
      ))
    return (
      <div
        className={`flex flex-row gap-1 items-center font-bold ${style} cursor-pointer`}
        onClick={onClickHeader}
      >
        <div>{title}</div>
        <SortingArrow i={i} />
      </div>
    )
  }

  return (
    <div className="flex rounded flex-col border-2 border-red-400 pb-2">
      <div className="bg-red-500 p-2 font-bold text-white">{title}</div>
      <div className="flex flex-row p-2 gap-2 px-4">
        {
          <ColumnHeader
            i={-1}
            title="#"
            style="w-10"
            naturalOrderAscending={true}
          />
        }
        {columns.map((col, i) => (
          <ColumnHeader
            i={i}
            title={col.title}
            style={col.style}
            naturalOrderAscending={col.naturalOrderAscending}
          />
        ))}
      </div>
      {sortedValues.map(
        (val, i) =>
          (extended || i < numberToShow) && (
            <div
              className={`p-2 flex flex-row gap-2 px-4 ${
                i > 0 ? "border-t-2" : ""
              }`}
              key={getKey(val.value)}
            >
              {
                <div className="w-10">
                  <div>{val.originalRank + 1}</div>
                </div>
              }
              {columns.map((col) => (
                <div
                  key={`${getKey(val.value)}-${col.title}`}
                  className={col.style}
                >
                  {col.getValue(val.value)}
                </div>
              ))}
            </div>
          )
      )}
      <div
        className="p-2 px-4 cursor-pointer hover:underline"
        onClick={onClickToggleExtended}
      >
        {!extended ? "Show more..." : "Show fewer..."}
      </div>
    </div>
  )
}

export const StationStats = (props: { stats: StationStat[] }) => {
  let { stats } = props
  let stationColumn: TableColumn<StationStat> = {
    style: "w-96",
    title: "Station",
    getValue: (stn) => (
      <div className="flex flex-row gap-2">
        <div className="font-bold w-12">{stn.crs}</div>
        <div>{stn.name}</div>
      </div>
    ),
    getOrder: (t1, t2, natural) =>
      sortBy(t1, t2, getSorter(StationStatSorter.byName, natural)),
    naturalOrderAscending: true,
  }
  let operatorColumn: TableColumn<StationStat> = {
    style: "w-72",
    title: "Operator",
    getValue: (stn) => stn.operatorName,
    getOrder: (t1, t2, natural) =>
      sortBy(
        t1,
        t2,
        getSorter(StationStatSorter.byOperator, natural),
        getSorter(StationStatSorter.byName, natural)
      ),
    naturalOrderAscending: true,
  }
  let boardsColumn: TableColumn<StationStat> = {
    style: "w-14",
    title: "B",
    getValue: (stn) => stn.boards,
    getOrder: (stn1, stn2, natural) =>
      sortBy(
        stn1,
        stn2,
        getSorter(StationStatSorter.byBoards, !natural),
        getSorter(StationStatSorter.byAlights, !natural),
        getSorter(StationStatSorter.byCalls, !natural),
        getSorter(StationStatSorter.byName, true)
      ),
    naturalOrderAscending: false,
  }
  let alightsColumn: TableColumn<StationStat> = {
    style: "w-14",
    title: "A",
    getValue: (stn) => stn.alights,
    getOrder: (stn1, stn2, natural) =>
      sortBy(
        stn1,
        stn2,
        getSorter(StationStatSorter.byAlights, !natural),
        getSorter(StationStatSorter.byBoards, !natural),
        getSorter(StationStatSorter.byCalls, !natural),
        getSorter(StationStatSorter.byName, true)
      ),
    naturalOrderAscending: false,
  }
  let boardsPlusAlightsColumn: TableColumn<StationStat> = {
    style: "w-14",
    title: "B+A",
    getValue: (stn) => stn.boards + stn.alights,
    getOrder: (stn1, stn2, natural) =>
      sortBy(
        stn1,
        stn2,
        getSorter(StationStatSorter.byBoardsPlusAlights, !natural),
        getSorter(StationStatSorter.byBoards, !natural),
        getSorter(StationStatSorter.byAlights, !natural),
        getSorter(StationStatSorter.byCalls, !natural),
        getSorter(StationStatSorter.byName, true)
      ),
    naturalOrderAscending: false,
  }
  let callsColumn: TableColumn<StationStat> = {
    style: "w-14",
    title: "C",
    getValue: (stn) => stn.intermediates,
    getOrder: (stn1, stn2, natural) =>
      sortBy(
        stn1,
        stn2,
        getSorter(StationStatSorter.byCalls, !natural),
        getSorter(StationStatSorter.byBoards, !natural),
        getSorter(StationStatSorter.byAlights, !natural),
        getSorter(StationStatSorter.byName, true)
      ),
    naturalOrderAscending: false,
  }
  let totalColumn: TableColumn<StationStat> = {
    style: "w-14",
    title: "T",
    getValue: (stn) => stn.boards + stn.alights + stn.intermediates,
    getOrder: (stn1, stn2, natural) =>
      sortBy(
        stn1,
        stn2,
        getSorter(StationStatSorter.byTotal, !natural),
        getSorter(StationStatSorter.byBoards, !natural),
        getSorter(StationStatSorter.byAlights, !natural),
        getSorter(StationStatSorter.byCalls, !natural),
        getSorter(StationStatSorter.byName, true)
      ),
    naturalOrderAscending: false,
  }
  let columns = [
    stationColumn,
    operatorColumn,
    boardsColumn,
    alightsColumn,
    boardsPlusAlightsColumn,
    callsColumn,
    totalColumn,
  ]
  return (
    <SortableTable
      title="Stations"
      columns={columns}
      values={stats}
      numberToShow={10}
      getKey={(stn) => stn.crs}
      rankSort={(stn1, stn2, natural) =>
        sortBy(
          stn1,
          stn2,
          getSorter(StationStatSorter.byBoardsPlusAlights, !natural),
          getSorter(StationStatSorter.byBoards, !natural),
          getSorter(StationStatSorter.byAlights, !natural),
          getSorter(StationStatSorter.byCalls, !natural),
          getSorter(StationStatSorter.byName, true)
        )
      }
    />
  )
}

export const LegList = (props: { legs: TrainLeg[] }) =>
  props.legs.map((leg, i) => (
    <div className="flex flex-col gap-2" key={i}>
      <hr className="h-px border-0 bg-gray-600" />
      <LegRow key={leg.id} leg={leg} />
    </div>
  ))
