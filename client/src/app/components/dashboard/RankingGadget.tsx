import { getLongDate, getShortDate } from "@/app/utils/datetime"
import { TransportUserTrainLegOutData } from "@/app/utils/train"

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
        <div className="flex flex-col md:flex-row text-2xl font-bold gap-2 md:gap-0">
          <div className="flex-1 line-clamp-2">
            {`${leg.board_station.station_name} to ${leg.alight_station.station_name}`}
          </div>
          <div className="md:w-36 md:text-right">{getStatValue(leg)}</div>
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
    <div className="flex flex-col md:flex-row px-4 gap-1 md:gap-0">
      <div className="w-20">{getShortDate(leg.start_datetime)}</div>
      <div className="flex-1 line-clamp-2 lg:line-clamp-none lg:truncate">
        {leg.board_station.station_name} to {leg.alight_station.station_name}
      </div>
      <div className="md:w-32 md:text-right">{getStatValue(leg)}</div>
    </div>
  )
}

interface LegRankingGadgetProps {
  legs: TransportUserTrainLegOutData[]
  title: string
  colour: string
  getStatValue: (leg: TransportUserTrainLegOutData) => string
}

export const LegRankingGadget = ({
  legs,
  title,
  colour,
  getStatValue,
}: LegRankingGadgetProps) =>
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
      {/* <div className="flex flex-col gap-4 md:gap-2 py-2 bg-white">
        {legs.slice(1).map((leg) => (
          <OtherLeg key={leg.leg_id} leg={leg} getStatValue={getStatValue} />
        ))}
      </div> */}
    </div>
  )

interface HeadlineItemProps<T> {
  item: T
  title: string
  colour: string
  getItemName: (t: T) => string
  getStatValue: (t: T) => string
}

const HeadlineItem = <T,>({
  item,
  title,
  colour,
  getItemName,
  getStatValue,
}: HeadlineItemProps<T>) => {
  return (
    <div
      className="flex flex-row text-white p-4"
      style={{ backgroundColor: colour }}
    >
      <div className="w-full flex flex-col gap-2">
        <div className="font-bold">{title}</div>
        <div className="flex flex-col md:flex-row text-2xl font-bold gap-2 md:gap-0">
          <div className="flex-1 line-clamp-2">{getItemName(item)}</div>
          <div className="md:w-36 md:text-right">{getStatValue(item)}</div>
        </div>
      </div>
    </div>
  )
}

interface GenericRankingGadgetProps<T> {
  items: T[]
  title: string
  colour: string
  getItemName: (t: T) => string
  getStatValue: (t: T) => string
}

export const GenericRankingGadget = <T,>({
  items,
  title,
  colour,
  getItemName,
  getStatValue,
}: GenericRankingGadgetProps<T>) =>
  items[0] && (
    <div
      className={`flex flex-col lg:w-1/2 rounded-xl border-2 overflow-hidden ${colour}`}
      style={{ borderWidth: 2, borderColor: colour }}
    >
      <HeadlineItem
        item={items[0]}
        title={title}
        colour={colour}
        getItemName={getItemName}
        getStatValue={getStatValue}
      />
      {/* <div className="flex flex-col gap-4 md:gap-2 py-2 bg-white">
        {legs.slice(1).map((leg) => (
          <OtherLeg key={leg.leg_id} leg={leg} getStatValue={getStatValue} />
        ))}
      </div> */}
    </div>
  )
