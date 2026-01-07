import { getMilesAndChainsString } from "@/app/structs"
import { getLongDate, getShortDate } from "@/app/utils/datetime"
import { TransportUserTrainLegOutData } from "@/app/utils/leg"

interface HeadlineLegStationNameProps {
  stationName: string
  stationCrs: string
}

const HeadlineLegStationName = ({
  stationName,
  stationCrs,
}: HeadlineLegStationNameProps) => {
  return (
    <div className="flex flex-col items-center w-52">
      <div className="text-xl font-bold">{stationCrs}</div>
      <div>{stationName}</div>
    </div>
  )
}

interface HeadlineLegProps {
  leg: TransportUserTrainLegOutData
}

const HeadlineLeg = ({ leg }: HeadlineLegProps) => {
  return (
    <div className="flex flex-row bg-green-800 text-white p-4">
      <div className="flex flex-col gap-2">
        <div className="font-bold">Longest leg by distance</div>
        <div className="text-lg">{getLongDate(leg.start_datetime)}</div>
        <div className="text-2xl font-bold">
          {leg.board_station.station_name} to {leg.alight_station.station_name}
        </div>
        <div>{getMilesAndChainsString(Number(leg.distance))}</div>
      </div>
    </div>
  )
}

interface OtherLegProps {
  leg: TransportUserTrainLegOutData
}

const OtherLeg = ({ leg }: OtherLegProps) => {
  return (
    <div className="flex flex-row px-4">
      <div className="w-20">{getShortDate(leg.start_datetime)}</div>
      <div className="w-96">
        {leg.board_station.station_name} to {leg.alight_station.station_name}
      </div>
      <div className="w-32 text-right">
        {getMilesAndChainsString(Number(leg.distance))}
      </div>
    </div>
  )
}

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
      <div className="text-lg">Distance</div>
      <div className="flex flex-row gap-4">
        {longestDistanceLegs.length > 0 && (
          <div className="flex flex-col rounded-xl border-2 border-green-800 overflow-hidden">
            <HeadlineLeg leg={longestDistanceLegs[0]} />
            <div className="flex flex-col gap-2 py-2">
              {longestDistanceLegs.slice(1).map((leg) => (
                <OtherLeg leg={leg} />
              ))}
            </div>
          </div>
        )}
        {shortestDistanceLegs.length > 0 && (
          <div className="flex flex-col rounded-xl border-2 border-green-800 overflow-hidden">
            <HeadlineLeg leg={shortestDistanceLegs[0]} />
            <div className="flex flex-col gap-2 py-2">
              {shortestDistanceLegs.slice(1).map((leg) => (
                <OtherLeg leg={leg} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default DistanceStatsPane
