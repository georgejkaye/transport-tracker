import { RankingGadget } from "@/app/components/dashboard/RankingGadget"
import { getMilesAndChainsString } from "@/app/utils/distance"
import { TransportUserTrainLegOutData } from "@/app/utils/leg"

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
        <RankingGadget
          legs={longestDistanceLegs}
          title="Longest by distance"
          colour="#166534"
          getStatValue={(leg) => getMilesAndChainsString(Number(leg.distance))}
        />
        <RankingGadget
          legs={shortestDistanceLegs}
          title="Shortest by distance"
          colour="#166534"
          getStatValue={(leg) => getMilesAndChainsString(Number(leg.distance))}
        />
      </div>
    </div>
  )
}

export default DistanceStatsPane
