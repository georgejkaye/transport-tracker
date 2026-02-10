import { Duration } from "js-joda"

export const getDurationStringFromString = (duration: string) =>
  getDurationStringFromDuration(Duration.parse(duration))

export const getDurationStringFromDuration = (duration: Duration) => {
  let days = Math.floor(duration.toDays())
  let hours = Math.floor(duration.toHours()) % 24
  let minutes = Math.round(duration.toMinutes()) % 60
  let dayString = days ? `${days}d ` : ""
  return `${dayString}${hours}h ${minutes}m`
}
