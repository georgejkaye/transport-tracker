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

export const getDurationStringFromMinutes = (minutes: number) => {
  let dayCount = Math.floor(minutes / 1440)
  let hourCount = Math.floor(minutes / 60) % 24
  let minuteCount = minutes % 60
  let dayString = dayCount ? `${dayCount}d ` : ""
  return `${dayString}${hourCount}h ${minuteCount}m`
}
