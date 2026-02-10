import { LegRankingGadget } from "@/app/components/dashboard/RankingGadget"
import { getMilesAndChainsStringFromNumber } from "@/app/utils/distance"
import { TransportUserTrainLegOutData } from "@/app/utils/train"

interface DistanceStatsPaneProps {
  longestDistanceLegs: TransportUserTrainLegOutData[]
  shortestDistanceLegs: TransportUserTrainLegOutData[]
}

export const DistanceStatsPane = ({
  longestDistanceLegs,
  shortestDistanceLegs,
}: DistanceStatsPaneProps) => {
  return (
    <div className="flex flex-col">
      <div className="flex flex-col lg:flex-row gap-4">
        <LegRankingGadget
          legs={longestDistanceLegs}
          title="Longest by distance"
          colour="#166534"
          getStatValue={(leg) =>
            getMilesAndChainsStringFromNumber(Number(leg.distance))
          }
        />
        <LegRankingGadget
          legs={shortestDistanceLegs}
          title="Shortest by distance"
          colour="#166534"
          getStatValue={(leg) =>
            getMilesAndChainsStringFromNumber(Number(leg.distance))
          }
        />
      </div>
    </div>
  )
}

export default DistanceStatsPane
