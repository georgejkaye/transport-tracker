"use client"

import { useEffect, useState } from "react"
import {
  dateToShortString,
  dateToTimeString,
  getLegDestination,
  getLegOrigin,
  getMilesAndChainsString,
  TrainLeg,
  TrainStation,
  TrainLegCall,
  durationToHoursAndMinutes,
  getDurationString,
} from "./structs"
import { getLegs } from "./data"
import { Delay, Duration } from "./leg"
import Link from "next/link"
import { linkStyle } from "./styles"
import TrainOutlinedIcon from "@mui/icons-material/TrainOutlined"
import { Loader } from "./loader"

const StationLink = (props: { station: TrainStation }) => {
  let { station } = props
  return (
    <div className="w-56 flex-wrap">
      <Link className={linkStyle} href={`/train/station/${station.crs}`}>
        {station.name}
      </Link>
    </div>
  )
}

const EndpointSection = (props: { call: TrainLegCall; origin: boolean }) => {
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

const LegRow = (props: { leg: TrainLeg }) => {
  let { leg } = props
  let mileString = !leg.distance ? "" : getMilesAndChainsString(leg.distance)
  let origin = getLegOrigin(leg)
  let destination = getLegDestination(leg)
  return (
    <div className="flex flex-row gap-4 justify-center">
      <div className="flex flex-col lg:flex-row gap-4">
        <div className="flex flex-row gap-2 lg:w-80 items-center">
          <Link className={linkStyle} href={`/train/leg/${leg.id}`}>
            <TrainOutlinedIcon />
          </Link>
          <div className="text-xs lg:hidden">•</div>
          <div className="lg:px-2">{dateToShortString(leg.start)}</div>
          <div className="text-xs lg:hidden">•</div>
          <div className="lg:w-28">{getDurationString(leg.duration)}</div>
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

const TotalStat = (props: { title: string; value: string }) => {
  let { title, value } = props
  return (
    <div className="flex flex-row">
      <div className="border-r border-gray-600 pr-2">{title}</div>
      <div className="pl-2">{value}</div>
    </div>
  )
}

const TotalLegStats = (props: { legs: TrainLeg[] }) => {
  let { legs } = props
  let { distance, duration } = legs.reduce(
    ({ distance, duration }, cur) => {
      let newDistance = !cur.distance ? 0 : cur.distance
      let newDuration = cur.duration
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
                <>
                  <LegRow leg={leg} key={i} />{" "}
                  {i === legs.length - 1 ? (
                    ""
                  ) : (
                    <hr className="h-px border-0 bg-gray-600" />
                  )}
                </>
              ))}
        </div>
      )}
    </div>
  )
}

export default Page
