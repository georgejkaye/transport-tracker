import { GenericRankingGadget } from "@/app/components/dashboard/RankingGadget"
import { TransportUserTrainClassHighOutData } from "@/app/utils/train"

interface ClassStatsPaneProps {
  topClasses: TransportUserTrainClassHighOutData[]
}

export const ClassStatsPane = ({ topClasses }: ClassStatsPaneProps) => {
  return (
    <div className="flex flex-col">
      <div className="flex flex-col lg:flex-row gap-4">
        <GenericRankingGadget
          items={topClasses}
          title="Top class (count)"
          colour="#760588"
          getItemName={(cls) =>
            `Class ${cls.class_no}${
              cls.class_name ? ` (${cls.class_name})` : ""
            }`
          }
          getStatValue={(cls) => `${cls.class_count} legs`}
        />
      </div>
    </div>
  )
}

export default ClassStatsPane
