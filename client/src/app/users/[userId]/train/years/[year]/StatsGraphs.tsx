import {
  TransportUserDetailsTrainLegYearOutData,
  TransportUserDetailsTrainStationYearOutData,
  TransportUserTrainOperatorYearStats,
} from "@/app/utils/train"
import { LineChart } from "@mui/x-charts/LineChart"
import { getMilesAndChainsStringFromNumber } from "@/app/utils/distance"
import { yellowPaletteDark } from "@mui/x-charts"
import { Duration } from "js-joda"
import { getDurationStringFromMinutes } from "@/app/utils/duration"

interface YearTaggedDatum {
  year: number
  value: number[]
}

interface YearTaggedSeriesStyle {
  name?: string
  colour?: string
}

interface YearGraphProps {
  title: string
  data: YearTaggedDatum[]
  style: YearTaggedSeriesStyle[]
  tooltipFormatter?: (value: number) => string
  axisFormatter?: (value: number) => string
  yAxisWidth: number
}

const YearGraph = ({
  title,
  data,
  style,
  tooltipFormatter,
  axisFormatter,
  yAxisWidth,
}: YearGraphProps) => {
  let sortedData = data.sort((datum) => datum.year)
  let yearLabels = sortedData.map((datum) =>
    datum.year.toString().replace(",", ""),
  )
  let seriesCount = sortedData[0]?.value.length ?? 0
  let yData = Array.from({ length: seriesCount }, (_, i) =>
    Array.from(
      { length: sortedData.length },
      (_, j) => sortedData[j]?.value[i] ?? 0,
    ),
  )
  return (
    <div className="flex-1 p-4 shadow-lg" style={{ height: "300px" }}>
      <h2 className="font-bold text-lg">{title}</h2>
      <LineChart
        series={yData.map((series, i) => ({
          data: series,
          id: style[i]?.name ?? `${title}-${i}`,
          valueFormatter: (x) =>
            !x ? "" : !tooltipFormatter ? `${x}` : tooltipFormatter(x),
          label: style[i]?.name,
          color: "#003366",
        }))}
        xAxis={[{ scaleType: "point", data: yearLabels, height: 28 }]}
        yAxis={[
          {
            id: "leftAxisId",
            valueFormatter: !axisFormatter
              ? (x: number) => `${x}`
              : axisFormatter,
            width: yAxisWidth,
          },
        ]}
        hideLegend
      />
    </div>
  )
}

interface StatsGraphsProps {
  trainLegStats: TransportUserDetailsTrainLegYearOutData[]
  trainStationStats: TransportUserDetailsTrainStationYearOutData[]
  trainOperatorStats: TransportUserTrainOperatorYearStats[]
}

const StatsGraphs = ({
  trainLegStats,
  trainStationStats,
  trainOperatorStats,
}: StatsGraphsProps) => {
  let legCountData = trainLegStats.map((yearData) => ({
    year: yearData.year,
    value: [yearData.count],
  }))
  let legDistanceData = trainLegStats.map((yearData) => ({
    year: yearData.year,
    value: [Number(yearData.total_distance)],
  }))
  let legDurationData = trainLegStats.map((yearData) => ({
    year: yearData.year,
    value: [Duration.parse(yearData.total_duration).toMinutes()],
  }))
  let stationCountData = trainStationStats.map((yearData) => ({
    year: yearData.year,
    value: [yearData.station_count, yearData.new_station_count],
  }))
  return (
    <div className="flex flex-col">
      <div className="flex flex-col md:flex-row">
        <YearGraph
          data={legCountData}
          title="Count"
          style={[{ name: "Count" }]}
          yAxisWidth={30}
        />
        <YearGraph
          data={legDistanceData}
          title="Distance"
          style={[{ name: "Distance" }]}
          tooltipFormatter={getMilesAndChainsStringFromNumber}
          axisFormatter={(x) => `${Math.floor(x)} mi`}
          yAxisWidth={60}
        />
        <YearGraph
          data={legDurationData}
          title="Duration"
          style={[{ name: "Duration" }]}
          tooltipFormatter={getDurationStringFromMinutes}
          axisFormatter={(x) => `${Math.floor(x / 60)} h`}
          yAxisWidth={40}
        />
      </div>
      <div>
        <YearGraph
          data={stationCountData}
          title="Stations"
          style={[{ name: "Total stations" }, { name: "New stations" }]}
          yAxisWidth={30}
        />
      </div>
    </div>
  )
}

export default StatsGraphs
