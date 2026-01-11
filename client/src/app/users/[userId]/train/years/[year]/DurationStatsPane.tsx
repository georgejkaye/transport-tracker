import { Duration } from "js-joda"

import { RankingGadget } from "@/app/components/dashboard/RankingGadget"
import { getDurationString } from "@/app/utils/duration"
import { TransportUserTrainLegOutData } from "@/app/utils/leg"

interface DurationStatsPaneProps {
  longestDurationLegs: TransportUserTrainLegOutData[]
  shortestDurationLegs: TransportUserTrainLegOutData[]
}

export const DurationStatsPane = ({
  longestDurationLegs,
  shortestDurationLegs,
}: DurationStatsPaneProps) => {
  return (
    <div className="flex flex-col">
      <div className="flex flex-row gap-4">
        <RankingGadget
          legs={longestDurationLegs}
          title="Longest by duration"
          colour="bg-green-800"
          getStatValue={(leg) =>
            getDurationString(Duration.parse(leg.duration))
          }
        />
        <RankingGadget
          legs={shortestDurationLegs}
          title="Shortest by duration"
          colour="bg-green-800"
          getStatValue={(leg) =>
            getDurationString(Duration.parse(leg.duration))
          }
        />
      </div>
    </div>
  )
}

export default DurationStatsPane
