import { getLongDate, getShortDate } from "@/app/utils/datetime"
import { TransportUserTrainLegOutData } from "@/app/utils/leg"

interface HeadlineLegProps {
  leg: TransportUserTrainLegOutData
  title: string
  colour: string
  getStatValue: (leg: TransportUserTrainLegOutData) => string
}

const HeadlineLeg = ({
  leg,
  title,
  colour,
  getStatValue,
}: HeadlineLegProps) => {
  return (
    <div
      className="flex flex-row text-white p-4"
      style={{ backgroundColor: colour }}
    >
      <div className="w-full flex flex-col gap-2">
        <div className="font-bold">{title}</div>
        <div className="text-lg">{getLongDate(leg.start_datetime)}</div>
        <div className="flex flex-row text-2xl font-bold">
          <div className="flex-1 line-clamp-2 md:line-clamp-none md:truncatet s">
            {`${leg.board_station.station_name} to ${leg.alight_station.station_name}`}
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
      <div className="flex-1 line-clamp-2 md:line-clamp-none md:truncate">
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
      className={`flex flex-col lg:w-1/2 rounded-xl border-2 overflow-hidden ${colour}`}
      style={{ borderWidth: 2, borderColor: colour }}
    >
      <HeadlineLeg
        leg={legs[0]}
        title={title}
        colour={colour}
        getStatValue={getStatValue}
      />
      <div className="flex flex-col gap-2 py-2 bg-white">
        {legs.slice(1).map((leg) => (
          <OtherLeg key={leg.leg_id} leg={leg} getStatValue={getStatValue} />
        ))}
      </div>
    </div>
  )
