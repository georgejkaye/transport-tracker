import { getMilesAndChainsString } from "@/app/utils/distance"
import { getDurationString } from "@/app/utils/duration"
import { Duration } from "js-joda"

interface TotalStatBoxProps {
  title: string
  value: number | string
}

const TotalStatBox = ({ title, value }: TotalStatBoxProps) => (
  <div className="rounded-xl bg-blue-900 text-white border-2 border-gray-100 flex flex-col py-4 px-8 w-96 gap-1">
    <div>{title}</div>
    <div className="text-2xl font-bold">{value}</div>
  </div>
)

interface TotalStatsPaneProps {
  count: number
  totalDistance: number | string
  totalDuration: string
  totalDelay: number
}

export const TotalStatsPane = ({
  count,
  totalDistance,
  totalDuration,
  totalDelay,
}: TotalStatsPaneProps) => {
  return (
    <div className="flex flex-row gap-4">
      <TotalStatBox title="Count" value={count} />
      <TotalStatBox
        title="Distance"
        value={getMilesAndChainsString(Number(totalDistance ?? 0))}
      />
      <TotalStatBox
        title="Duration"
        value={getDurationString(Duration.parse(totalDuration))}
      />
      <TotalStatBox title="Delay" value={totalDelay} />
    </div>
  )
}

export default TotalStatsPane
