import Link from "next/link"
import {
  dateToTimeString,
  maybeDateToTimeString,
  TrainLeg,
  TrainLegCall,
  TrainStation,
} from "./structs"
import { linkStyle } from "./styles"
import TrainOutlinedIcon from "@mui/icons-material/TrainOutlined"

export const LegIconLink = (props: { id: number }) => {
  let { id } = props
  return (
    <Link className={linkStyle} href={`/train/leg/${id}`}>
      <TrainOutlinedIcon />
    </Link>
  )
}

export const EndpointSection = (props: {
  call: TrainLegCall
  origin: boolean
}) => {
  let { call, origin } = props
  let planTime = origin ? call.planDep : call.planArr
  let actTime = origin ? call.actDep : call.actArr
  return (
    <div className="flex flex-row">
      <StationLink station={call.station} />
      <div className="flex flex-row gap-2">
        <div className="w-10 hidden">
          {!planTime ? "" : dateToTimeString(planTime)}
        </div>
        <div className="w-10">{!actTime ? "" : dateToTimeString(actTime)}</div>
        <Delay plan={planTime} act={actTime} />
      </div>
    </div>
  )
}

export const getDelay = (plan: Date, act: Date) => {
  let delay = (act.getTime() - plan.getTime()) / 1000 / 60
  let delayString =
    delay < 0 ? delay.toString() : delay > 0 ? `+${delay.toString()}` : "•"
  return {
    delay,
    text: delayString,
  }
}

export const PlanActTime = (props: { plan?: Date; act?: Date }) => {
  let { plan, act } = props
  return (
    <div className="flex flex-row">
      <div className="w-14 text-center">{maybeDateToTimeString(plan)}</div>
      <div className="w-14 text-center font-bold">
        {maybeDateToTimeString(act)}
      </div>
      <Delay plan={plan} act={act} />
    </div>
  )
}

export const getDelayOrUndefined = (
  plan: Date | undefined,
  act: Date | undefined
) => {
  if (!plan || !act) {
    return { delay: undefined, text: "" }
  }
  return getDelay(plan, act)
}

const getDelayStyle = (delay: number | undefined) =>
  delay === undefined
    ? ""
    : delay <= -5
    ? "text-green-600"
    : delay < 0
    ? "text-green-400"
    : delay === 0
    ? "text-gray-400"
    : delay < 5
    ? "text-red-400"
    : "text-red-600"

const getDurationString = (origin: Date, destination: Date) => {
  let duration = destination.getTime() - origin.getTime()
  return `${Math.floor(duration / 1000 / 60 / 60)
    .toString()
    .padStart(2, "0")}h ${((duration / 1000 / 60) % 60)
    .toString()
    .padStart(2, "0")}m`
}

export const Duration = (props: {
  origin: Date | undefined
  destination: Date | undefined
}) => {
  let { origin, destination } = props
  let durationString =
    !origin || !destination ? "" : getDurationString(origin, destination)
  return <div className="lg:w-32">{durationString}</div>
}

export const delayWidth = "w-10"

export const Delay = (props: {
  plan: Date | undefined
  act: Date | undefined
}) => {
  let { plan, act } = props
  let { delay, text } = getDelayOrUndefined(plan, act)
  let style = getDelayStyle(delay)
  return <div className={`${style} ${delayWidth} text-center`}>{text}</div>
}

export const ShortStationLink = (props: { station: TrainStation }) => {
  let { station } = props
  return (
    <div className="flex-1 flex-wrap">
      <Link className={linkStyle} href={`/train/station/${station.crs}`}>
        {station.name}
      </Link>
    </div>
  )
}

export const StationLink = (props: {
  station: TrainStation
  style?: string
}) => {
  let { station, style } = props
  let styleText = !style ? "" : style
  return (
    <div className="w-56 flex-wrap">
      <Link
        className={`${linkStyle} ${styleText}`}
        href={`/train/station/${station.crs}`}
      >
        {station.name}
      </Link>
    </div>
  )
}

export const TotalStat = (props: { title: string; value: string }) => {
  let { title, value } = props
  return (
    <div className="flex flex-row">
      <div className="border-r border-gray-600 pr-2">{title}</div>
      <div className="pl-2">{value}</div>
    </div>
  )
}
