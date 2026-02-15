import {
  TransportUserDetailsTrainLegOutData,
  TransportUserDetailsTrainStationOutData,
  TransportUserTrainOperatorStats,
  UserTrainYearStats,
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
    <div className="md:flex-1 py-4 shadow-lg" style={{ height: "300px" }}>
      <h2 className="font-bold text-lg px-4">{title}</h2>
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
  trainStats: UserTrainYearStats[]
}

const StatsGraphs = ({ trainStats }: StatsGraphsProps) => {
  let legCountData = trainStats.map((yearData) => ({
    year: yearData.year,
    value: [yearData.leg_stats.count],
  }))
  let legDistanceData = trainStats.map((yearData) => ({
    year: yearData.year,
    value: [Number(yearData.leg_stats.total_distance)],
  }))
  let legDurationData = trainStats.map((yearData) => ({
    year: yearData.year,
    value: [Duration.parse(yearData.leg_stats.total_duration).toMinutes()],
  }))
  let stationCountData = trainStats.map((yearData) => ({
    year: yearData.year,
    value: [
      yearData.station_stats.station_count,
      yearData.station_stats.new_station_count,
    ],
  }))
  let operatorCountData = trainStats.map((yearData) => ({
    year: yearData.year,
    value: [yearData.operator_stats.operator_count],
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
      <div className="flex flex-col md:flex-row">
        <YearGraph
          data={stationCountData}
          title="Stations"
          style={[{ name: "Total stations" }, { name: "New stations" }]}
          yAxisWidth={30}
        />
        <YearGraph
          data={operatorCountData}
          title="Operators"
          style={[{ name: "Total operators" }]}
          yAxisWidth={30}
        />
      </div>
    </div>
  )
}

export default StatsGraphs
