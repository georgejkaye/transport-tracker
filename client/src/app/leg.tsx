import { TrainLegCall } from "./structs"

export const getDelay = (plan: Date, act: Date) => {
  let delay = (act.getTime() - plan.getTime()) / 1000 / 60
  let delayString =
    delay < 0 ? delay.toString() : delay > 0 ? `+${delay.toString()}` : ""
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
  !delay
    ? ""
    : delay <= 5
    ? "text-green-500"
    : delay < 0
    ? "text-green-200"
    : delay === 0
    ? "text-white"
    : delay < 5
    ? "text-red-200"
    : "text-red-500"

const getDurationString = (origin: Date, destination: Date) => {
  let duration = destination.getTime() - origin.getTime()
  return `${Math.floor(duration / 1000 / 60 / 60)
    .toString()
    .padStart(2, "0")}:${((duration / 1000 / 60) % 60)
    .toString()
    .padStart(2, "0")}`
}

export const Duration = (props: {
  origin: Date | undefined
  destination: Date | undefined
}) => {
  let { origin, destination } = props
  let durationString =
    !origin || !destination ? "" : getDurationString(origin, destination)
  return <div className="w-10">{durationString}</div>
}

export const Delay = (props: {
  plan: Date | undefined
  act: Date | undefined
}) => {
  let { plan, act } = props
  let { delay, text } = getDelayOrUndefined(plan, act)
  let style = getDelayStyle(delay)
  return <div className={`${style} w-6 text-center`}>{text}</div>
}
