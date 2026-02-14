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
  longestLegDistanceText: string
  shortestLegDistance: string
  shortestLegDistanceText: string
  totalDelay: number
  longestLegDelay: number
  longestLegDelayText: string
  shortestLegDelay: number
  shortestLegDelayText: string
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
  mostOperatorDistance: string
  mostOperatorDistanceName: string
  mostOperatorDuration: string
  mostOperatorDurationName: string
  mostOperatorDelay: number
  mostOperatorDelayName: string
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
  longestLegDistanceText,
  shortestLegDistance,
  shortestLegDistanceText,
  totalDelay,
  longestLegDelay,
  longestLegDelayText,
  shortestLegDelay,
  shortestLegDelayText,
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
  mostOperatorDistance,
  mostOperatorDistanceName,
  mostOperatorDuration,
  mostOperatorDurationName,
  mostOperatorDelay,
  mostOperatorDelayName,
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
          label="Total distance"
          value={getMilesAndChainsStringFromString(totalDistance)}
        />
        <StatsRowWithText
          label="Longest distance"
          value={getMilesAndChainsStringFromString(longestLegDistance)}
          text={longestLegDistanceText}
        />
        <StatsRowWithText
          label="Shortest distance"
          value={getMilesAndChainsStringFromString(shortestLegDistance)}
          text={shortestLegDistanceText}
        />
        <StatsRow label="Total delay" value={getDelayString(totalDelay)} />
        <StatsRowWithText
          label="Longest"
          value={getDelayString(longestLegDelay)}
          text={longestLegDelayText}
        />
        <StatsRowWithText
          label="Shortest"
          value={getDelayString(shortestLegDelay)}
          text={shortestLegDelayText}
        />
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
        <StatsRowWithText
          label="Most duration"
          value={getDurationStringFromString(mostOperatorDuration)}
          text={mostOperatorDurationName}
        />
        <StatsRowWithText
          label="Most distance"
          value={getMilesAndChainsStringFromString(mostOperatorDistance)}
          text={mostOperatorDistanceName}
        />
        <StatsRowWithText
          label="Most delay"
          value={getDelayString(mostOperatorDelay)}
          text={mostOperatorDelayName}
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
  longestLegDistanceText,
  shortestLegDistance,
  shortestLegDistanceText,
  totalDelay,
  longestLegDelay,
  longestLegDelayText,
  shortestLegDelay,
  shortestLegDelayText,
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
  mostOperatorDistance,
  mostOperatorDistanceName,
  mostOperatorDuration,
  mostOperatorDurationName,
  mostOperatorDelay,
  mostOperatorDelayName,
}: OverallStatsTableProps) => {
  return (
    <div className="flex flex-col gap-4">
      <div className="font-bold text-xl">Overall</div>
      <StatsTable
        legCount={legCount}
        totalDuration={totalDuration}
        longestLegDuration={longestLegDuration}
        longestLegDurationText={longestLegDurationText}
        shortestLegDuration={shortestLegDuration}
        shortestLegDurationText={shortestLegDurationText}
        totalDistance={totalDistance}
        longestLegDistance={longestLegDistance}
        longestLegDistanceText={longestLegDistanceText}
        shortestLegDistance={shortestLegDistance}
        shortestLegDistanceText={shortestLegDistanceText}
        totalDelay={totalDelay}
        longestLegDelay={longestLegDelay}
        longestLegDelayText={longestLegDelayText}
        shortestLegDelay={shortestLegDelay}
        shortestLegDelayText={shortestLegDelayText}
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
        mostOperatorDistance={mostOperatorDistance}
        mostOperatorDistanceName={mostOperatorDistanceName}
        mostOperatorDuration={mostOperatorDuration}
        mostOperatorDurationName={mostOperatorDurationName}
        mostOperatorDelay={mostOperatorDelay}
        mostOperatorDelayName={mostOperatorDelayName}
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
    <div className="flex flex-col p-4 shadow-lg">
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
        longestLegDistanceText={
          trainStats.leg_stats_overall?.longest_distance?.text ?? ""
        }
        shortestLegDistance={
          trainStats.leg_stats_overall?.shortest_distance?.value ?? ""
        }
        shortestLegDistanceText={
          trainStats.leg_stats_overall?.shortest_distance?.text ?? ""
        }
        totalDelay={trainStats.leg_stats_overall?.total_delay ?? 0}
        longestLegDelay={
          trainStats.leg_stats_overall?.longest_delay?.value ?? 0
        }
        longestLegDelayText={
          trainStats.leg_stats_overall?.longest_delay?.text ?? ""
        }
        shortestLegDelay={
          trainStats.leg_stats_overall?.shortest_delay?.value ?? 0
        }
        shortestLegDelayText={
          trainStats.leg_stats_overall?.shortest_delay?.text ?? ""
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
        mostOperatorDuration={
          trainStats.operator_stats_overall?.longest_duration?.value ?? ""
        }
        mostOperatorDurationName={
          trainStats.operator_stats_overall?.longest_duration
            ?.operator_or_brand_name ?? ""
        }
        mostOperatorDistance={
          trainStats.operator_stats_overall?.longest_distance?.value ?? ""
        }
        mostOperatorDistanceName={
          trainStats.operator_stats_overall?.longest_distance
            ?.operator_or_brand_name ?? ""
        }
        mostOperatorDelay={
          trainStats.operator_stats_overall?.longest_delay?.value ?? 0
        }
        mostOperatorDelayName={
          trainStats.operator_stats_overall?.longest_delay
            ?.operator_or_brand_name ?? ""
        }
      />
    </div>
  )
}

export default StatsPane
