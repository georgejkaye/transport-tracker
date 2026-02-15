import { getDelayString } from "@/app/utils/delay"
import { getMilesAndChainsStringFromString } from "@/app/utils/distance"
import { getDurationStringFromString } from "@/app/utils/duration"
import {
  TransportUserDetailsTrainLegOutData,
  TransportUserDetailsTrainStationOutData,
  UserTrainYearStats,
  TransportUserTrainOperatorStats,
  UserTrainStats,
  UserTrainAllStats,
} from "@/app/utils/train"
import { useState } from "react"
import { FaAngleDown } from "react-icons/fa6"

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

interface StatWithLinkAndTimestamp<T> {
  value: T
  id: number
  text: string
  datetime: string
}

interface StatWithLink<T> {
  value: T
  id: number
  text: string
}

interface OperatorStat<T> {
  value: T
  operator_or_brand_id: number
  is_brand: boolean
  operator_or_brand_name: string
}

interface StatsTableProps {
  legCount: number
  totalDuration: string
  longestDurationLeg?: StatWithLinkAndTimestamp<string> | null
  shortestDurationLeg?: StatWithLinkAndTimestamp<string> | null
  totalDistance: string
  longestDistanceLeg?: StatWithLinkAndTimestamp<string> | null
  shortestDistanceLeg?: StatWithLinkAndTimestamp<string> | null
  totalDelay: number
  mostDelayedLeg?: StatWithLinkAndTimestamp<number> | null
  leastDelayedLeg?: StatWithLinkAndTimestamp<number> | null
  stationCount: number
  newStationCount?: number
  mostVisitedStation?: StatWithLink<number> | null
  mostBoardedStation?: StatWithLink<number> | null
  mostAlightedStation?: StatWithLink<number> | null
  operatorCount: number
  mostUsedOperator: OperatorStat<number> | null
  longestDistanceOperator?: OperatorStat<string> | null
  longestDurationOperator?: OperatorStat<string> | null
  mostDelayedOperator?: OperatorStat<number> | null
}

const StatsTable = ({
  legCount,
  totalDuration,
  longestDurationLeg,
  shortestDurationLeg,
  totalDistance,
  longestDistanceLeg,
  shortestDistanceLeg,
  totalDelay,
  mostDelayedLeg,
  leastDelayedLeg,
  stationCount,
  newStationCount,
  mostVisitedStation,
  mostBoardedStation,
  mostAlightedStation,
  operatorCount,
  mostUsedOperator,
  longestDistanceOperator,
  longestDurationOperator,
  mostDelayedOperator,
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
        {longestDurationLeg && (
          <StatsRowWithText
            label={"Longest duration"}
            value={getDurationStringFromString(longestDurationLeg.value)}
            text={longestDurationLeg.text}
          />
        )}
        {shortestDurationLeg && (
          <StatsRowWithText
            label={"Shortest duration"}
            value={getDurationStringFromString(shortestDurationLeg.value)}
            text={shortestDurationLeg.text}
          />
        )}
        <StatsRow
          label="Total distance"
          value={getMilesAndChainsStringFromString(totalDistance)}
        />
        {longestDistanceLeg && (
          <StatsRowWithText
            label="Longest distance"
            value={getMilesAndChainsStringFromString(longestDistanceLeg.value)}
            text={longestDistanceLeg.text}
          />
        )}
        {shortestDistanceLeg && (
          <StatsRowWithText
            label="Shortest distance"
            value={getMilesAndChainsStringFromString(shortestDistanceLeg.value)}
            text={shortestDistanceLeg.text}
          />
        )}
        <StatsRow label="Total delay" value={getDelayString(totalDelay)} />
        {mostDelayedLeg && (
          <StatsRowWithText
            label="Longest"
            value={getDelayString(mostDelayedLeg.value)}
            text={mostDelayedLeg.text}
          />
        )}
        {leastDelayedLeg && (
          <StatsRowWithText
            label="Shortest"
            value={getDelayString(leastDelayedLeg.value)}
            text={leastDelayedLeg.text}
          />
        )}
      </div>
      <StatsTableSubheader title="Stations" />
      <div className="flex flex-col gap-2">
        <StatsRow label="Count" value={stationCount} />
        {newStationCount && (
          <StatsRow label="New stations" value={newStationCount} />
        )}
        {mostVisitedStation && (
          <StatsRowWithText
            label="Most visits"
            value={mostVisitedStation.value}
            text={mostVisitedStation.text}
          />
        )}
        {mostBoardedStation && (
          <StatsRowWithText
            label="Most boards"
            value={mostBoardedStation.value}
            text={mostBoardedStation.text}
          />
        )}
        {mostAlightedStation && (
          <StatsRowWithText
            label="Most alights"
            value={mostAlightedStation.value}
            text={mostAlightedStation.text}
          />
        )}
      </div>
      <StatsTableSubheader title="Operators" />
      <div className="flex flex-col gap-2">
        <StatsRow label="Count" value={operatorCount} />
        {mostUsedOperator && (
          <StatsRowWithText
            label="Most journeys"
            value={mostUsedOperator.value}
            text={mostUsedOperator.operator_or_brand_name}
          />
        )}
        {longestDurationOperator && (
          <StatsRowWithText
            label="Most duration"
            value={getDurationStringFromString(longestDurationOperator.value)}
            text={longestDurationOperator.operator_or_brand_name}
          />
        )}
        {longestDistanceOperator && (
          <StatsRowWithText
            label="Most distance"
            value={getMilesAndChainsStringFromString(
              longestDistanceOperator.value,
            )}
            text={longestDistanceOperator.operator_or_brand_name}
          />
        )}
        {mostDelayedOperator && (
          <StatsRowWithText
            label="Most delay"
            value={getDelayString(mostDelayedOperator.value)}
            text={mostDelayedOperator.operator_or_brand_name}
          />
        )}
      </div>
    </div>
  )
}

interface OverallStatsTableProps {
  stats: UserTrainStats
}

const OverallStatsTable = ({ stats }: OverallStatsTableProps) => {
  return (
    <div className="flex flex-col gap-4 p-4 shadow-lg w-1/2">
      <div className="font-bold text-xl">Overall</div>
      <StatsTable
        legCount={stats.leg_stats.count}
        totalDuration={stats.leg_stats.total_duration}
        longestDurationLeg={stats.leg_stats.longest_duration}
        shortestDurationLeg={stats.leg_stats.shortest_duration}
        totalDistance={stats.leg_stats.total_distance}
        longestDistanceLeg={stats.leg_stats.longest_distance}
        shortestDistanceLeg={stats.leg_stats.shortest_distance}
        totalDelay={stats.leg_stats.total_delay ?? 0}
        mostDelayedLeg={stats.leg_stats.longest_delay}
        leastDelayedLeg={stats.leg_stats.shortest_delay}
        stationCount={stats.station_stats.station_count}
        mostVisitedStation={stats.station_stats.most_boards_and_alights_station}
        mostBoardedStation={stats.station_stats.most_boards_station}
        mostAlightedStation={stats.station_stats.most_alights_station}
        operatorCount={stats.operator_stats.operator_count}
        mostUsedOperator={stats.operator_stats.greatest_count}
        longestDurationOperator={stats.operator_stats.longest_duration}
        longestDistanceOperator={stats.operator_stats.longest_distance}
        mostDelayedOperator={stats.operator_stats.longest_delay}
      />
    </div>
  )
}

type YearlyStatsTableProps = {
  stats: UserTrainYearStats[]
}

const YearlyStatsTable = ({ stats }: YearlyStatsTableProps) => {
  const sortedStats = stats.sort((a, b) => -(a.year - b.year))
  const [currentStats, setCurrentStats] = useState(sortedStats[0])
  const [isChoosingYear, setChoosingYear] = useState(false)
  const onClickYear = (yearlyStats: UserTrainYearStats) => {
    setCurrentStats(yearlyStats)
    setChoosingYear(false)
  }
  return (
    <div className="flex flex-col gap-4 p-4 shadow-lg w-1/2">
      {currentStats && (
        <>
          <div className="font-bold text-xl flex flex-row">
            <div className="flex-1">{currentStats.year}</div>
            <button>
              <FaAngleDown onClick={() => setChoosingYear((cur) => !cur)} />
            </button>
          </div>
          {isChoosingYear ? (
            <div className="flex flex-col gap-4">
              {sortedStats.map((yearlyStats) => (
                <button
                  className="text-right"
                  onClick={() => onClickYear(yearlyStats)}
                >
                  {yearlyStats.year}
                </button>
              ))}
            </div>
          ) : (
            <StatsTable
              legCount={currentStats.leg_stats.count}
              totalDuration={currentStats.leg_stats.total_duration}
              longestDurationLeg={currentStats.leg_stats.longest_duration}
              shortestDurationLeg={currentStats.leg_stats.shortest_duration}
              totalDistance={currentStats.leg_stats.total_distance}
              longestDistanceLeg={currentStats.leg_stats.longest_distance}
              shortestDistanceLeg={currentStats.leg_stats.shortest_distance}
              totalDelay={currentStats.leg_stats.total_delay ?? 0}
              mostDelayedLeg={currentStats.leg_stats.longest_delay}
              leastDelayedLeg={currentStats.leg_stats.shortest_delay}
              stationCount={currentStats.station_stats.station_count}
              mostVisitedStation={
                currentStats.station_stats.most_boards_and_alights_station
              }
              mostBoardedStation={
                currentStats.station_stats.most_boards_station
              }
              mostAlightedStation={
                currentStats.station_stats.most_alights_station
              }
              operatorCount={currentStats.operator_stats.operator_count}
              mostUsedOperator={currentStats.operator_stats.greatest_count}
              longestDurationOperator={
                currentStats.operator_stats.longest_duration
              }
              longestDistanceOperator={
                currentStats.operator_stats.longest_distance
              }
              mostDelayedOperator={currentStats.operator_stats.longest_delay}
            />
          )}
        </>
      )}
    </div>
  )
}

interface StatsPaneProps {
  trainStats: UserTrainAllStats
}

const StatsPane = ({ trainStats }: StatsPaneProps) => {
  return (
    <div className="flex flex-col md:flex-row flex-1">
      <OverallStatsTable stats={trainStats.overall_stats} />
      <YearlyStatsTable stats={trainStats.year_stats} />
    </div>
  )
}

export default StatsPane
