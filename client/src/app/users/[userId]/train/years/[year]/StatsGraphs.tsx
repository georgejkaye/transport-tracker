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
  value: number
}

interface YearGraphProps {
  title: string
  data: YearTaggedDatum[]
  popupFormatter: (value: number) => string
  axisFormatter: (value: number) => string
  yAxisWidth: number
}

const YearGraph = ({
  title,
  data,
  popupFormatter,
  axisFormatter,
  yAxisWidth,
}: YearGraphProps) => {
  let sortedData = data.sort((datum) => datum.year)
  let yearLabels = sortedData.map((datum) =>
    datum.year.toString().replace(",", ""),
  )
  let yData = sortedData.map((datum) => datum.value)
  return (
    <div className="flex-1 p-4 shadow-lg" style={{ height: "300px" }}>
      <h2 className="font-bold text-lg">{title}</h2>
      <LineChart
        series={[
          {
            data: yData,
            id: title,
            valueFormatter: (x) => (!x ? "" : popupFormatter(x)),
            color: "#003366",
          },
        ]}
        xAxis={[{ scaleType: "point", data: yearLabels, height: 28 }]}
        yAxis={[
          {
            id: "leftAxisId",
            valueFormatter: axisFormatter,
            width: yAxisWidth,
          },
        ]}
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
    value: yearData.count,
  }))
  let legDistanceData = trainLegStats.map((yearData) => ({
    year: yearData.year,
    value: Number(yearData.total_distance),
  }))
  let legDurationData = trainLegStats.map((yearData) => ({
    year: yearData.year,
    value: Duration.parse(yearData.total_duration).toMinutes(),
  }))
  return (
    <div className="flex flex-col md:flex-row">
      <YearGraph
        data={legCountData}
        title="Count"
        popupFormatter={(x) => `${x}`}
        axisFormatter={(x) => `${x}`}
        yAxisWidth={30}
      />
      <YearGraph
        data={legDistanceData}
        title="Distance"
        popupFormatter={getMilesAndChainsStringFromNumber}
        axisFormatter={(x) => `${Math.floor(x)} mi`}
        yAxisWidth={60}
      />
      <YearGraph
        data={legDurationData}
        title="Duration"
        popupFormatter={getDurationStringFromMinutes}
        axisFormatter={(x) => `${Math.floor(x / 60)} h`}
        yAxisWidth={40}
      />
    </div>
  )
}

export default StatsGraphs
