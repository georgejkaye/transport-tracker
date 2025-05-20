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

export const LegIconLink = (props: { userId: number; legId: number }) => {
  let { userId, legId } = props
  return (
    <Link className={linkStyle} href={`/users/${userId}/train/legs/${legId}`}>
      <TrainOutlinedIcon />
    </Link>
  )
}

export const EndpointSection = (props: {
  userId: number
  call: TrainLegCall
  origin: boolean
}) => {
  let { userId, call, origin } = props
  let planTime = origin ? call.planDep : call.planArr
  let actTime = origin ? call.actDep : call.actArr
  return (
    <div className="flex flex-row">
      <StationLink userId={userId} station={call.station} />
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

export const getDelayString = (delay: number) =>
  delay < 0 ? delay.toString() : delay > 0 ? `+${delay.toString()}` : "•"

export const getDelay = (plan: Date, act: Date) => {
  let delay = (act.getTime() - plan.getTime()) / 1000 / 60
  let delayString = getDelayString(delay)
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

export const getDelayStyle = (delay: number | undefined) =>
  delay === undefined
    ? ""
    : delay <= -5
    ? "#43a047"
    : delay < 0
    ? "#66bb6a"
    : delay === 0
    ? "#bdbdbd"
    : delay < 5
    ? "#ef5350"
    : "#e53935"

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
  return (
    <div className={`${delayWidth} text-center`} style={{ color: style }}>
      {text}
    </div>
  )
}

export const ShortStationLink = (props: {
  userId: number
  station: TrainStation
}) => {
  let { userId, station } = props
  return (
    <div className="flex-1 flex-wrap">
      <Link
        className={linkStyle}
        href={`/users/${userId}/train/stations/${station.crs}`}
      >
        {station.name}
      </Link>
    </div>
  )
}

export const StationLink = (props: {
  userId: number
  station: TrainStation
  style?: string
}) => {
  let { userId, station, style } = props
  let styleText = !style ? "" : style
  return (
    <div className="w-56 flex-wrap">
      <Link
        className={`${linkStyle} ${styleText}`}
        href={`/users/${userId}/train/stations/${station.crs}`}
      >
        {station.name}
      </Link>
    </div>
  )
}

export const TotalStat = (props: { title: string; value: string }) => {
  let { title, value } = props
  return (
    <div className="flex flex-row text-lg bg-blue-200 p-4 align-baseline rounded">
      <div className="">{title}</div>
      <div className="pl-2 font-bold text-xl">{value}</div>
    </div>
  )
}
