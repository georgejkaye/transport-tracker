"use client"

import Image from "next/image"
import { useEffect, useState } from "react"
import {
  dateToShortString,
  dateToTimeString,
  getLegDestination,
  getLegOrigin,
  getMilesAndChainsString,
  mileageToMilesAndChains,
  TrainLeg,
  TrainStation,
  TrainLegCall,
} from "./structs"
import { getLegs } from "./data"
import { Delay, Duration } from "./leg"
import Link from "next/link"
import { linkStyle } from "./styles"

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
    <div className="flex flex-row gap-4">
      <div className="flex flex-col lg:flex-row gap-2">
        <div className="flex flex-row gap-2 lg:w-72 items-center">
          <Link
            className={linkStyle}
            href={`/train/leg/${leg.id}`}
          >{`#${leg.id}`}</Link>
          <div className="flex-1">{dateToShortString(leg.start)}</div>
          <Duration origin={origin.actDep} destination={destination.actArr} />
          <div className="text-xs lg:hidden">•</div>
          <div className="text-right lg:w-32  ">{mileString}</div>
        </div>
        <div className="flex flex-col md:flex-row gap-2">
          <div className="flex flex-row gap-2 items-center">
            <div className="text-right w-10 text-xs">from</div>
            <EndpointSection call={origin} origin={true} />
          </div>
          <div className="flex flex-row gap-2 items-center">
            <div className="text-right w-10 text-xs">to</div>
            <EndpointSection call={destination} origin={false} />
          </div>
        </div>
      </div>
      {/* <Duration origin={origin.planDep} destination={destination.planArr} />
       */}
    </div>
  )
}

export default function Home() {
  const [legs, setLegs] = useState<TrainLeg[]>([])
  useEffect(() => {
    const getLegData = async () => {
      let legData = await getLegs()
      setLegs(legData)
    }
    getLegData()
  }, [])
  return (
    <main className="flex min-h-screen flex-col items-center justify-between">
      <div className="flex flex-col gap-4">
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
    </main>
  )
}
