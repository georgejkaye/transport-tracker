"use client"

import Image from "next/image"

import { getTrainStationData } from "@/app/data"
import { Loader } from "@/app/loader"
import {
  dateToShortString,
  dateToTimeString,
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
  LegIconLink,
  PlanActTime,
} from "@/app/leg"
import { linkStyle } from "@/app/styles"
import Link from "next/link"

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

const StationLeg = (props: { crs: string; leg: TrainStationLegData }) => {
  let { crs, leg } = props
  return (
    <div className="flex flex-col md:flex-row gap-2 justify-center items-center">
      <div className="flex flex-row gap-2 items-center">
        <LegIconLink id={leg.id} />
        <div className="w-28 text-center">
          {dateToShortString(leg.stopTime)}
        </div>
      </div>
      <div className="flex flex-col md:flex-row gap-2">
        <StationLegEndpoint
          crs={crs}
          station={leg.origin}
          origin={true}
          plan={leg.planArr}
          act={leg.actArr}
        />
        <StationLegEndpoint
          crs={crs}
          station={leg.destination}
          origin={false}
          plan={leg.planDep}
          act={leg.actDep}
        />
      </div>
    </div>
  )
}

const StationLegs = (props: { crs: string; legs: TrainStationLegData[] }) => {
  let { crs, legs } = props
  return (
    <div className="flex flex-col gap-2">
      <h2 className="font-bold text-xl">Leg calls</h2>
      {legs.map((leg, i) => (
        <div key={i} className="flex flex-col gap-2">
          <Line />
          <StationLeg crs={crs} leg={leg} />
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
      <h1 className="text-2xl font-bold flex gap-2">
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
      <StationLegs crs={station.crs} legs={station.legs} />
    </div>
  )
}

export default Page
