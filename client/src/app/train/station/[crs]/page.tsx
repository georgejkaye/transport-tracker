"use client"

import Image from "next/image"

import { getTrainStationData } from "@/app/data"
import { Loader } from "@/app/loader"
import {
  dateToShortString,
  dateToTimeString,
  maybeDateToTimeString,
  TrainStation,
  TrainStationData,
  TrainStationLegData,
} from "@/app/structs"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { Line } from "@/app/line"
import {
  Delay,
  delayWidth,
  EndpointSection,
  getDelay,
  LegIconLink,
  PlanActTime,
  StationLink,
} from "@/app/leg"
import { linkStyle } from "@/app/styles"
import Link from "next/link"
import {
  LineDashed,
  StartTerminusSymbol,
  StationSymbol,
  EndTerminusSymbol,
} from "@/app/svgs"

const StationLegEndpoint = (props: {
  crs: string
  station: TrainStation
  origin: boolean
  plan?: Date
  act?: Date
}) => {
  let { crs, station, origin, plan, act } = props
  let endpointFlavourText = origin ? "from" : "to"
  let stationNameStyle = "w-48"
  return (
    <div className="flex flex-row gap-2 items-center">
      <div className="text-right w-10 text-xs md:hidden">
        {endpointFlavourText}
      </div>
      {station.crs === crs ? (
        <div className={`font-bold ${stationNameStyle}`}>{station.name}</div>
      ) : (
        <Link
          href={`/train/station/${station.crs}`}
          className={`${linkStyle} ${stationNameStyle}`}
        >
          {station.name}
        </Link>
      )}
      <div className="w-10">
        {station.crs === crs ? "" : !plan ? "" : dateToTimeString(plan)}
      </div>
      <div className="w-10">
        {station.crs === crs ? "" : !act ? "" : dateToTimeString(act)}
      </div>
      {station.crs === crs ? (
        <div className={delayWidth} />
      ) : (
        <Delay plan={plan} act={act} />
      )}
    </div>
  )
}

const StationLegPlanActTime = (props: { plan?: Date; act?: Date }) => {
  let { plan, act } = props
  return (
    <div className="flex flex-row">
      <div className="w-16 text-center">{maybeDateToTimeString(plan)}</div>
      <div className="w-16 text-center">{maybeDateToTimeString(act)}</div>
      <Delay plan={plan} act={act} />
    </div>
  )
}

const StationLeg = (props: {
  station: TrainStation
  leg: TrainStationLegData
}) => {
  let { station, leg } = props
  let startsAtThisStation = leg.origin.crs === station.crs
  let terminatesAtThisStation = leg.destination.crs === station.crs
  return (
    <div className="flex flex-col md:flex-row gap-2 w-full">
      <div className="px-4">
        <div className="flex flex-row gap-2 items-center">
          <LegIconLink id={leg.id} />
          <div className="w-28 text-center text-left">
            {dateToShortString(leg.stopTime)}
          </div>
        </div>
        <div className="flex flex-col md:flex-row w-full px-1">
          {leg.origin.crs === station.crs ? (
            ""
          ) : (
            <div className="flex flex-row items-center gap-2">
              <div className="w-14 text-left">
                {maybeDateToTimeString(leg.actArr ?? leg.planArr)}
              </div>
              <div className="w-8 text-sm text-right">from</div>
              <StationLink station={leg.origin} />
            </div>
          )}
          {leg.destination.crs === station.crs ? (
            ""
          ) : (
            <div className="flex flex-row items-center gap-2">
              <div className="w-14 text-left">
                {maybeDateToTimeString(leg.actDep ?? leg.planDep)}
              </div>
              <div className="w-8 text-sm text-right">to</div>
              <StationLink station={leg.destination} />
            </div>
          )}
        </div>
      </div>
      <div className="bg-red-300 text-white px-4">West Midlands Railway</div>
    </div>
  )
}

const StationLegs = (props: {
  station: TrainStation
  legs: TrainStationLegData[]
}) => {
  let { station, legs } = props
  return (
    <div className="flex flex-col gap-2">
      <Line />
      {legs.map((leg, i) => (
        <div key={i} className="flex flex-col">
          <StationLeg station={station} leg={leg} />
          <Line />
        </div>
      ))}
    </div>
  )
}

const Page = ({ params }: { params: { crs: string } }) => {
  let { crs } = params
  let router = useRouter()
  let [station, setStation] = useState<TrainStationData | undefined>(undefined)
  useEffect(() => {
    const getStationData = async () => {
      let stationData = await getTrainStationData(crs)
      if (!stationData) {
        router.push("/")
      } else {
        setStation(stationData)
      }
    }
    getStationData()
  }, [])
  return !station ? (
    <Loader />
  ) : (
    <div className="flex flex-col gap-2">
      <div className="px-4">
        <h1 className="text-3xl font-bold flex gap-2">
          <span className="text-gray-700">{station.crs}</span>
          <span>{station.name}</span>
        </h1>
        <div>{station.brand ? station.brand.name : station.operator.name}</div>
        {!station.img ? (
          ""
        ) : (
          <>
            <Image
              className="my-2 rounded"
              src={station.img}
              height={500}
              width={500}
              alt={`Station sign for ${station.name}`}
            />
          </>
        )}
      </div>
      <StationLegs station={station} legs={station.legs} />
    </div>
  )
}

export default Page
