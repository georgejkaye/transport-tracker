import { getDelayString } from "@/app/utils/delay"
import { getMilesAndChainsString } from "@/app/utils/distance"
import { getDurationString } from "@/app/utils/duration"
import { Duration } from "js-joda"

interface TotalStatBoxProps {
  title: string
  value: number | string
}

const TotalStatBox = ({ title, value }: TotalStatBoxProps) => (
  <div className="rounded-xl bg-blue-900 text-white border-2 border-blue-700 flex flex-col flex-1 py-4 px-4 gap-1">
    <div>{title}</div>
    <div className="text-2xl font-bold">{value}</div>
  </div>
)

interface TotalStatsPaneProps {
  count: number
  totalDistance: number | string
  totalDuration: string
  totalDelay: number
  operatorCount: number
  classCount: number
  unitCount: number
}

export const TotalStatsPane = ({
  count,
  totalDistance,
  totalDuration,
  totalDelay,
  operatorCount,
  classCount,
  unitCount,
}: TotalStatsPaneProps) => {
  return (
    <div className="w-full flex flex-col gap-4">
      <div className="w-full flex flex-col lg:flex-row gap-4">
        <div className="w-full flex flex-row gap-4">
          <TotalStatBox title="Count" value={count} />
          <TotalStatBox
            title="Distance"
            value={getMilesAndChainsString(Number(totalDistance ?? 0))}
          />
        </div>
        <div className="w-full grow flex flex-row gap-4">
          <TotalStatBox
            title="Duration"
            value={getDurationString(Duration.parse(totalDuration))}
          />
          <TotalStatBox title="Delay" value={getDelayString(totalDelay)} />
        </div>
      </div>
      <div>
        <div className="w-full grow flex flex-row gap-4">
          <TotalStatBox title="Operators" value={operatorCount} />
          <TotalStatBox title="Classes" value={classCount} />
          <TotalStatBox title="Units" value={unitCount} />
        </div>
      </div>
    </div>
  )
}

export default TotalStatsPane
