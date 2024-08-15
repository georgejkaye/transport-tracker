import { TrainLegCall } from "./structs"

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
  return <div>{durationString}</div>
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
