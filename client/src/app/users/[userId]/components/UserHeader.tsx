import { getMilesAndChainsStringFromNumber } from "@/app/utils/distance"
import { getDurationStringFromString } from "@/app/utils/duration"
import { UserTrainStats } from "@/app/utils/train"
import { FaBusSimple, FaTrain } from "react-icons/fa6"

interface UserHeaderProps {
  trainStats: UserTrainStats
  userName: string
  displayName: string
}

const UserHeader = ({ trainStats, userName, displayName }: UserHeaderProps) => {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-bold">{displayName}</h1>
        <div>@{userName}</div>
      </div>
      <div className="flex flex-col md:flex-row gap-4 items-left">
        <div className="flex flex-row gap-4 items-center p-4 shadow-lg">
          <FaTrain />
          <div>{trainStats.leg_stats.count}</div>
          <div>
            {getMilesAndChainsStringFromNumber(
              Number(trainStats.leg_stats.total_distance),
            )}
          </div>
          {trainStats.leg_stats.total_duration && (
            <div>
              {getDurationStringFromString(trainStats.leg_stats.total_duration)}
            </div>
          )}
        </div>
        <div className="flex flex-row gap-4 items-center p-4 shadow-lg">
          <FaBusSimple />
          <div>-</div>
        </div>
      </div>
    </div>
  )
}

export default UserHeader
