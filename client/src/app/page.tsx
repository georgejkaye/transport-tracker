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
} from "./structs"
import { getLegs } from "./data"

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
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <div className="flex flex-col gap-2">
        {!legs
          ? ""
          : legs.map((leg, i) => {
              let mileString = !leg.distance
                ? ""
                : getMilesAndChainsString(leg.distance)
              let origin = getLegOrigin(leg)
              let destination = getLegDestination(leg)
              return (
                <div key={i} className="flex flex-row gap-4">
                  <div>{dateToShortString(leg.start)}</div>
                  <div className="w-72">{origin.station.name}</div>
                  <div className="w-10">
                    {!origin.planDep ? "" : dateToTimeString(origin.planDep)}
                  </div>
                  <div className="w-10">
                    {!origin.actDep ? "" : dateToTimeString(origin.actDep)}
                  </div>
                  <div className="w-72">{destination.station.name}</div>
                  <div className="w-10">
                    {!destination.planArr
                      ? ""
                      : dateToTimeString(destination.planArr)}
                  </div>
                  <div className="w-10">
                    {!destination.actArr
                      ? ""
                      : dateToTimeString(destination.actArr)}
                  </div>
                  <div>{mileString}</div>
                </div>
              )
            })}
      </div>
    </main>
  )
}
