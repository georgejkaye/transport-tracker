import { GenericRankingGadget } from "@/app/components/dashboard/RankingGadget"
import { TransportUserTrainOperatorHighOutData } from "@/app/utils/train"

interface OperatorStatsPaneProps {
  topOperators: TransportUserTrainOperatorHighOutData[]
}

export const OperatorStatsPane = ({ topOperators }: OperatorStatsPaneProps) => {
  return (
    <div className="flex flex-col">
      <div className="flex flex-col lg:flex-row gap-4">
        <GenericRankingGadget
          items={topOperators}
          title="Top operator (count)"
          colour="#880505"
          getItemName={(operator) => operator.operator_name}
          getStatValue={(operator) => `${operator.leg_count} legs`}
        />
      </div>
    </div>
  )
}

export default OperatorStatsPane
