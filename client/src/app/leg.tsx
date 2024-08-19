import Link from "next/link"
import { TrainLegCall, TrainStation } from "./structs"
import { linkStyle } from "./styles"

export const getDelay = (plan: Date, act: Date) => {
  let delay = (act.getTime() - plan.getTime()) / 1000 / 60
  let delayString =
    delay < 0 ? delay.toString() : delay > 0 ? `+${delay.toString()}` : "•"
  return {
    delay,
    text: delayString,
  }
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

export const Delay = (props: {
  plan: Date | undefined
  act: Date | undefined
}) => {
  let { plan, act } = props
  let { delay, text } = getDelayOrUndefined(plan, act)
  let style = getDelayStyle(delay)
  return <div className={`${style} w-10 text-center`}>{text}</div>
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

export const StationLink = (props: { station: TrainStation }) => {
  let { station } = props
  return (
    <div className="w-56 flex-wrap">
      <Link className={linkStyle} href={`/train/station/${station.crs}`}>
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
