import { getMilesAndChainsString } from "@/app/structs"
import { getLongDate, getShortDate } from "@/app/utils/datetime"
import { TransportUserTrainLegOutData } from "@/app/utils/leg"
import { truncateString } from "@/app/utils/string"

interface HeadlineLegProps {
  leg: TransportUserTrainLegOutData
  title: string
  getStatValue: (leg: TransportUserTrainLegOutData) => string
}

const HeadlineLeg = ({ leg, title, getStatValue }: HeadlineLegProps) => {
  return (
    <div className="flex flex-row bg-green-800 text-white p-4">
      <div className="w-full flex flex-col gap-2">
        <div className="font-bold">{title}</div>
        <div className="text-lg">{getLongDate(leg.start_datetime)}</div>
        <div className="flex flex-row text-2xl font-bold">
          <div className="flex-1">
            {truncateString(
              `${leg.board_station.station_name} to ${leg.alight_station.station_name}`,
              40
            )}
          </div>
          <div className="w-36 text-right">{getStatValue(leg)}</div>
        </div>
      </div>
    </div>
  )
}

interface OtherLegProps {
  leg: TransportUserTrainLegOutData
  getStatValue: (leg: TransportUserTrainLegOutData) => string
}

const OtherLeg = ({ leg, getStatValue }: OtherLegProps) => {
  return (
    <div className="flex flex-row px-4">
      <div className="w-20">{getShortDate(leg.start_datetime)}</div>
      <div className="flex-1">
        {leg.board_station.station_name} to {leg.alight_station.station_name}
      </div>
      <div className="w-32 text-right">{getStatValue(leg)}</div>
    </div>
  )
}

interface RankingGadgetProps {
  legs: TransportUserTrainLegOutData[]
  title: string
  colour: string
  getStatValue: (leg: TransportUserTrainLegOutData) => string
}

export const RankingGadget = ({
  legs,
  title,
  colour,
  getStatValue,
}: RankingGadgetProps) =>
  legs[0] && (
    <div
      className={`flex flex-col w-1/2 rounded-xl border-2 border-green-800 overflow-hidden ${colour}`}
    >
      <HeadlineLeg leg={legs[0]} title={title} getStatValue={getStatValue} />
      <div className="flex flex-col gap-2 py-2 bg-white">
        {legs.slice(1).map((leg) => (
          <OtherLeg key={leg.leg_id} leg={leg} getStatValue={getStatValue} />
        ))}
      </div>
    </div>
  )
