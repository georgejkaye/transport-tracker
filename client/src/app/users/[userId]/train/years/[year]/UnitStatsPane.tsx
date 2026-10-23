import { GenericRankingGadget } from "@/app/components/dashboard/RankingGadget"
import { TransportUserTrainUnitHighOutData } from "@/app/utils/train"

interface UnitStatsPaneProps {
  topUnits: TransportUserTrainUnitHighOutData[]
}

export const UnitStatsPane = ({ topUnits }: UnitStatsPaneProps) => {
  console.log(topUnits)
  return (
    <div className="flex flex-col">
      <div className="flex flex-col lg:flex-row gap-4">
        <GenericRankingGadget
          items={topUnits}
          title="Top unit (count)"
          colour="#760588"
          getItemName={(unit) => `${unit.unit_number}`}
          getStatValue={(unit) => `${unit.unit_count} legs`}
        />
      </div>
    </div>
  )
}

export default UnitStatsPane
