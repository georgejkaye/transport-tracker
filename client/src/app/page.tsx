"use client"

import { useEffect, useState } from "react"
import {
  dateToShortString,
  getLegDestination,
  getLegOrigin,
  getMilesAndChainsString,
  TrainLeg,
  durationToHoursAndMinutes,
  getDurationString,
  getMaybeDurationString,
} from "./structs"
import { getLegs } from "./data"
import { EndpointSection, LegIconLink, TotalStat } from "./leg"
import { Loader } from "./loader"

const LegRow = (props: { leg: TrainLeg }) => {
  let { leg } = props
  let mileString = !leg.distance ? "" : getMilesAndChainsString(leg.distance)
  let origin = getLegOrigin(leg)
  let destination = getLegDestination(leg)
  return (
    <div className="flex flex-row gap-4 justify-center">
      <div className="flex flex-col lg:flex-row gap-4">
        <div className="flex flex-row gap-2 lg:w-80 items-center">
          <LegIconLink id={leg.id} />
          <div className="text-xs lg:hidden">•</div>
          <div className="lg:px-2">{dateToShortString(leg.start)}</div>
          <div className="text-xs lg:hidden">•</div>
          <div className="lg:w-28">{getMaybeDurationString(leg.duration)}</div>
          <div className="text-xs lg:hidden">•</div>
          <div className="lg:w-32">{mileString}</div>
        </div>
        <div className="flex flex-col md:flex-row gap-2">
          <div className="flex flex-row gap-2 items-center">
            <div className="text-right w-10 text-xs lg:hidden">from</div>
            <EndpointSection call={origin} origin={true} />
          </div>
          <div className="flex flex-row gap-2 items-center">
            <div className="text-right w-10 text-xs lg:hidden">to</div>
            <EndpointSection call={destination} origin={false} />
          </div>
        </div>
      </div>
      {/* <Duration origin={origin.planDep} destination={destination.planArr} />
       */}
    </div>
  )
}

const TotalLegStats = (props: { legs: TrainLeg[] }) => {
  let { legs } = props
  let { distance, duration } = legs.reduce(
    ({ distance, duration }, cur) => {
      let newDistance = !cur.distance ? 0 : cur.distance
      let newDuration = !cur.duration ? 0 : cur.duration
      return {
        distance: distance + newDistance,
        duration: duration + newDuration,
      }
    },
    { distance: 0, duration: 0 }
  )
  let { hours, minutes } = durationToHoursAndMinutes(duration)
  return (
    <div className="flex flex-row flex-wrap gap-4 justify-center">
      <TotalStat title="Legs" value={`${legs.length}`} />
      <TotalStat title="Distance" value={getMilesAndChainsString(distance)} />
      <TotalStat title="Duration" value={getDurationString(duration)} />
    </div>
  )
}

const Page = () => {
  const [legs, setLegs] = useState<TrainLeg[] | undefined>(undefined)
  useEffect(() => {
    const getLegData = async () => {
      let legData = await getLegs()
      setLegs(legData)
    }
    getLegData()
  }, [])
  return (
    <div>
      {legs === undefined ? (
        <Loader />
      ) : (
        <div className="flex flex-col gap-4">
          <TotalLegStats legs={legs} />
          {!legs
            ? ""
            : legs.map((leg, i) => (
                <div className="flex flex-col gap-2" key={i}>
                  <hr className="h-px border-0 bg-gray-600" />
                  <LegRow leg={leg} />
                </div>
              ))}
        </div>
      )}
    </div>
  )
}

export default Page
