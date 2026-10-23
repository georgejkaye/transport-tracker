import { Duration } from "js-joda"

import { LegRankingGadget } from "@/app/components/dashboard/RankingGadget"
import { getDurationStringFromDuration } from "@/app/utils/duration"
import { TransportUserTrainLegOutData } from "@/app/utils/train"
import { legendClasses } from "@mui/x-charts"

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
      <div className="flex flex-col lg:flex-row gap-4">
        <LegRankingGadget
          legs={longestDurationLegs}
          title="Longest by duration"
          colour="#166534"
          getStatValue={(leg) =>
            !leg.duration
              ? ""
              : getDurationStringFromDuration(Duration.parse(leg.duration))
          }
        />
        <LegRankingGadget
          legs={shortestDurationLegs}
          title="Shortest by duration"
          colour="#166534"
          getStatValue={(leg) =>
            !leg.duration
              ? ""
              : getDurationStringFromDuration(Duration.parse(leg.duration))
          }
        />
      </div>
    </div>
  )
}

export default DurationStatsPane
