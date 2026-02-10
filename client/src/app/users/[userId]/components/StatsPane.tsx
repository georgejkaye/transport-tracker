import { getDelayString } from "@/app/utils/delay"
import { getMilesAndChainsStringFromString } from "@/app/utils/distance"
import { getDurationStringFromString } from "@/app/utils/duration"
import { TransportUserDetailsTrainYearOutData } from "@/app/utils/train"

interface StatsRowProps {
  label: string
  value: string | number
}

const StatsRow = ({ label, value }: StatsRowProps) => {
  return (
    <div className="flex flex-row">
      <div className="w-3/5">{label}</div>
      <div className="w-2/5">{value}</div>
    </div>
  )
}

interface StatsRowWithTextProps {
  label: string
  value: string | number
  text: string
}

const StatsRowWithText = ({ label, value, text }: StatsRowWithTextProps) => {
  return (
    <div className="flex flex-col">
      <StatsRow label={label} value={value} />
      <div className="text-gray-500 text-sm">{text}</div>
    </div>
  )
}

interface StatsTableSubheaderProps {
  title: string
}

const StatsTableSubheader = ({ title }: StatsTableSubheaderProps) => (
  <div className="font-bold border-b-2 pb-2">{title}</div>
)

interface StatsTableProps {
  legCount: number
  totalDuration: string
  longestLegDuration: string
  longestLegDurationText: string
  shortestLegDuration: string
  shortestLegDurationText: string
  totalDistance: string
  longestLegDistance: string
  shortestLegDistance: string
  totalDelay: number
  longestLegDelay: number
  shortestLegDelay: number
  stationCount: number
  newStationCount?: number
  mostVisitedStationCount: number
  mostVisitedStationName: string
  mostBoardedStationCount: number
  mostBoardedStationName: string
  mostAlightedStationCount: number
  mostAlightedStationName: string
  operatorCount: number
  mostUsedOperatorCount: number
  mostUsedOperator: string
}

const StatsTable = ({
  legCount,
  totalDuration,
  longestLegDuration,
  longestLegDurationText,
  shortestLegDuration,
  shortestLegDurationText,
  totalDistance,
  longestLegDistance,
  shortestLegDistance,
  totalDelay,
  longestLegDelay,
  shortestLegDelay,
  stationCount,
  newStationCount,
  mostVisitedStationCount,
  mostVisitedStationName,
  mostBoardedStationCount,
  mostBoardedStationName,
  mostAlightedStationCount,
  mostAlightedStationName,
  operatorCount,
  mostUsedOperatorCount,
  mostUsedOperator,
}: StatsTableProps) => {
  return (
    <div className="flex flex-col gap-4">
      <StatsTableSubheader title="Journeys" />
      <div className="flex flex-col gap-2">
        <StatsRow label={"Count"} value={legCount} />
        <StatsRow
          label={"Total duration"}
          value={getDurationStringFromString(totalDuration)}
        />
        <StatsRowWithText
          label={"Longest duration"}
          value={getDurationStringFromString(longestLegDuration)}
          text={longestLegDurationText}
        />
        <StatsRowWithText
          label={"Shortest duration"}
          value={getDurationStringFromString(shortestLegDuration)}
          text={shortestLegDurationText}
        />
        <StatsRow
          label="Distance"
          value={getMilesAndChainsStringFromString(totalDistance)}
        />
        <StatsRow
          label="(Longest)"
          value={getMilesAndChainsStringFromString(longestLegDistance)}
        />
        <StatsRow
          label="(Shortest)"
          value={getMilesAndChainsStringFromString(shortestLegDistance)}
        />
        <StatsRow label="Delay" value={getDelayString(totalDelay)} />
        <StatsRow label="(Longest)" value={getDelayString(longestLegDelay)} />
        <StatsRow label="(Shortest)" value={getDelayString(shortestLegDelay)} />
      </div>
      <StatsTableSubheader title="Stations" />
      <div className="flex flex-col gap-2">
        <StatsRow label="Count" value={stationCount} />
        <StatsRowWithText
          label="Most visits"
          value={mostVisitedStationCount}
          text={mostVisitedStationName}
        />
        <StatsRowWithText
          label="Most boards"
          value={mostBoardedStationCount}
          text={mostBoardedStationName}
        />
        <StatsRowWithText
          label="Most alights"
          value={mostAlightedStationCount}
          text={mostAlightedStationName}
        />
      </div>
      <StatsTableSubheader title="Operators" />
      <div className="flex flex-col gap-2">
        <StatsRow label="Count" value={operatorCount} />
        <StatsRowWithText
          label="Most journeys"
          value={mostUsedOperatorCount}
          text={mostUsedOperator}
        />
      </div>
    </div>
  )
}

type OverallStatsTableProps = Omit<StatsTableProps, "newStationCount">

const OverallStatsTable = ({
  legCount,
  totalDuration,
  longestLegDuration,
  longestLegDurationText,
  shortestLegDuration,
  shortestLegDurationText,
  totalDistance,
  longestLegDistance,
  shortestLegDistance,
  totalDelay,
  longestLegDelay,
  shortestLegDelay,
  stationCount,
  mostVisitedStationCount,
  mostVisitedStationName,
  mostBoardedStationCount,
  mostBoardedStationName,
  mostAlightedStationCount,
  mostAlightedStationName,
  operatorCount,
  mostUsedOperatorCount,
  mostUsedOperator,
}: OverallStatsTableProps) => {
  return (
    <div className="flex flex-col gap-4">
      <div className="font-bold text-lg">Overall</div>
      <StatsTable
        legCount={legCount}
        totalDuration={totalDuration}
        longestLegDuration={longestLegDuration}
        longestLegDurationText={longestLegDurationText}
        shortestLegDuration={shortestLegDuration}
        shortestLegDurationText={shortestLegDurationText}
        totalDistance={totalDistance}
        longestLegDistance={longestLegDistance}
        shortestLegDistance={shortestLegDistance}
        totalDelay={totalDelay}
        longestLegDelay={longestLegDelay}
        shortestLegDelay={shortestLegDelay}
        stationCount={stationCount}
        mostVisitedStationCount={mostVisitedStationCount}
        mostVisitedStationName={mostVisitedStationName}
        mostBoardedStationCount={mostBoardedStationCount}
        mostBoardedStationName={mostBoardedStationName}
        mostAlightedStationCount={mostAlightedStationCount}
        mostAlightedStationName={mostAlightedStationName}
        operatorCount={operatorCount}
        mostUsedOperatorCount={mostUsedOperatorCount}
        mostUsedOperator={mostUsedOperator}
      />
    </div>
  )
}

type YearlyStatsTableProps = { year: number } & StatsTableProps

interface StatsPaneProps {
  trainStats: TransportUserDetailsTrainYearOutData
}

const StatsPane = ({ trainStats }: StatsPaneProps) => {
  return (
    <div className="flex flex-col p-4">
      <OverallStatsTable
        legCount={trainStats.leg_stats_overall?.count ?? 0}
        totalDuration={trainStats.leg_stats_overall?.total_duration ?? ""}
        longestLegDuration={
          trainStats.leg_stats_overall?.longest_duration?.value ?? ""
        }
        longestLegDurationText={
          trainStats.leg_stats_overall?.longest_duration?.text ?? ""
        }
        shortestLegDuration={
          trainStats.leg_stats_overall?.shortest_duration?.value ?? ""
        }
        shortestLegDurationText={
          trainStats.leg_stats_overall?.shortest_duration?.text ?? ""
        }
        totalDistance={trainStats.leg_stats_overall?.total_distance ?? ""}
        longestLegDistance={
          trainStats.leg_stats_overall?.longest_distance?.value ?? ""
        }
        shortestLegDistance={
          trainStats.leg_stats_overall?.shortest_distance?.value ?? ""
        }
        totalDelay={trainStats.leg_stats_overall?.total_delay ?? 0}
        longestLegDelay={
          trainStats.leg_stats_overall?.longest_delay?.value ?? 0
        }
        shortestLegDelay={
          trainStats.leg_stats_overall?.shortest_delay?.value ?? 0
        }
        stationCount={trainStats.station_stats_overall?.station_count ?? 0}
        mostVisitedStationCount={
          trainStats.station_stats_overall?.most_boards_and_alights_station
            ?.value ?? 0
        }
        mostVisitedStationName={
          trainStats.station_stats_overall?.most_boards_and_alights_station
            ?.text ?? ""
        }
        mostBoardedStationCount={
          trainStats.station_stats_overall?.most_boards_station?.value ?? 0
        }
        mostBoardedStationName={
          trainStats.station_stats_overall?.most_boards_station?.text ?? ""
        }
        mostAlightedStationCount={
          trainStats.station_stats_overall?.most_alights_station?.value ?? 0
        }
        mostAlightedStationName={
          trainStats.station_stats_overall?.most_alights_station?.text ?? ""
        }
        operatorCount={trainStats.operator_stats_overall?.operator_count ?? 0}
        mostUsedOperatorCount={
          trainStats.operator_stats_overall?.greatest_count?.value ?? 0
        }
        mostUsedOperator={
          trainStats.operator_stats_overall?.greatest_count
            ?.operator_or_brand_name ?? ""
        }
      />
    </div>
  )
}

export default StatsPane
