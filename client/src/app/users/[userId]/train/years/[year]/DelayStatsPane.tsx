import { RankingGadget } from "@/app/components/dashboard/RankingGadget"
import { getDelayString } from "@/app/utils/delay"
import { TransportUserTrainLegOutData } from "@/app/utils/leg"

interface DelayStatsPaneProps {
  longestDelayLegs: TransportUserTrainLegOutData[]
  shortestDelayLegs: TransportUserTrainLegOutData[]
}

export const DelayStatsPane = ({
  longestDelayLegs,
  shortestDelayLegs,
}: DelayStatsPaneProps) => {
  return (
    longestDelayLegs[0] &&
    longestDelayLegs[0].delay && (
      <div className="flex flex-col">
        <div className="flex flex-col lg:flex-row gap-4">
          <RankingGadget
            legs={longestDelayLegs}
            title="Longest by delay"
            colour="#166534"
            getStatValue={(leg) =>
              leg.delay === null ? "" : getDelayString(leg.delay)
            }
          />
          <RankingGadget
            legs={shortestDelayLegs}
            title="Shortest by delay"
            colour="#166534"
            getStatValue={(leg) =>
              leg.delay === null ? "" : getDelayString(leg.delay)
            }
          />
        </div>
      </div>
    )
  )
}

export default DelayStatsPane
