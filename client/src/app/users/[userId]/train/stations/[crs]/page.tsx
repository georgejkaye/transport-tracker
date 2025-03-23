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
import { Delay, delayWidth, LegIconLink, PlanActTime } from "@/app/leg"
import { linkStyle } from "@/app/styles"
import Link from "next/link"

const StationLegEndpoint = (props: {
  userId: number
  crs: string
  station: TrainStation
  origin: boolean
  plan?: Date
  act?: Date
}) => {
  let { userId, crs, station, origin, plan, act } = props
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
          href={`/users/${userId}/train/station/${station.crs}`}
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

interface StationLegProps {
  userId: number
  leg: TrainStationLegData
  originStyle: string
  destinationStyle: string
  operatorText: string
  operatorBg: string
  operatorFg: string
  passStyle: string
}

const StationLegMobile = ({
  userId,
  leg,
  originStyle,
  destinationStyle,
  operatorText,
  operatorBg,
  operatorFg,
  passStyle,
}: StationLegProps) => (
  <div
    className={`flex flex-col mx-4 gap-1 border-2 border-gray-400 rounded-xl overflow-hidden ${passStyle}`}
  >
    <div className="flex flex-row gap-4 m-2 p-1 align-center">
      <LegIconLink userId={userId} legId={leg.id} />
      <div className="flex flex-col md:flex-row flex-1">
        <div>
          <div className="flex flex-row gap-2 items-center pb-2">
            <div className="w-28 text-left flex-1">
              {dateToShortString(leg.stopTime)}
            </div>
            {!leg.actArr ? "" : <div>{`${dateToTimeString(leg.actArr)}`}</div>}
            {!leg.actDep ? "" : <div>{`${dateToTimeString(leg.actDep)}`}</div>}
            <div>{!leg.platform ? "" : `P${leg.platform}`}</div>
          </div>
          <div className="flex flex-col md:flex-row w-full">
            <div className="flex flex-row gap-1">
              <Link
                className={`${originStyle} ${linkStyle}`}
                href={`/users/${userId}/train/station/${leg.origin.crs}`}
              >
                {leg.origin.name}
              </Link>
              <div>to</div>
              <Link
                className={`${destinationStyle} ${linkStyle}`}
                href={`/users/${userId}/train/station/${leg.destination.crs}`}
              >
                {leg.destination.name}
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div
      className="px-4 py-1"
      style={{ background: operatorBg, color: operatorFg }}
    >
      {operatorText}
    </div>
  </div>
)

const StationLegWide = ({
  userId,
  leg,
  originStyle,
  destinationStyle,
  operatorText,
  operatorBg,
  operatorFg,
  passStyle,
}: StationLegProps) => (
  <div className="flex flex-row rounded-xl border-2 border-gray-300 mx-2 gap-2 overflow-hidden">
    <div className="flex flex-row p-2">
      {" "}
      <LegIconLink userId={userId} legId={leg.id} />
      <div className="w-28">{dateToShortString(leg.stopTime)}</div>
      <Link
        className={`${originStyle} ${linkStyle}`}
        href={`/users/${userId}/train/station/${leg.origin.crs}`}
      >
        {leg.origin.name}
      </Link>
      <PlanActTime plan={leg.planArr} act={leg.actArr} />
      <Link
        className={`${destinationStyle} ${linkStyle}`}
        href={`/users/${userId}/train/station/${leg.destination.crs}`}
      >
        {leg.destination.name}
      </Link>
      <PlanActTime plan={leg.planDep} act={leg.actDep} />
    </div>
    <div
      className="align-end p-2"
      style={{ background: operatorBg, color: operatorFg }}
    >
      {operatorText}
    </div>
  </div>
)

const StationLeg = (props: {
  userId: number
  station: TrainStation
  leg: TrainStationLegData
}) => {
  let { userId, station, leg } = props
  let boardsAtThisStation = leg.origin.crs === station.crs
  let alightsAtThisStation = leg.destination.crs === station.crs
  let operatorText = leg.brand ? leg.brand.name : leg.operator.name
  let operatorBg = leg.brand ? leg.brand.bg : leg.operator.bg
  let operatorFg = leg.brand ? leg.brand.fg : leg.operator.fg
  let passStyle =
    boardsAtThisStation || alightsAtThisStation ? "" : "bg-gray-300"
  let originStyle = boardsAtThisStation ? "font-bold" : ""
  let destinationStyle = alightsAtThisStation ? "font-bold" : ""
  return (
    <div>
      <div className="md:hidden">
        <StationLegMobile
          userId={userId}
          leg={leg}
          originStyle={originStyle}
          destinationStyle={destinationStyle}
          operatorText={operatorText}
          operatorBg={operatorBg}
          operatorFg={operatorFg}
          passStyle={passStyle}
        />
      </div>
      <div className="hidden md:block">
        <StationLegWide
          userId={userId}
          leg={leg}
          originStyle={originStyle}
          destinationStyle={destinationStyle}
          operatorText={operatorText}
          operatorBg={operatorBg}
          operatorFg={operatorFg}
          passStyle={passStyle}
        />
      </div>
    </div>
  )
}

const StationLegs = (props: {
  userId: number
  station: TrainStation
  legs: TrainStationLegData[]
}) => {
  let { userId, station, legs } = props
  return (
    <div className="flex flex-col gap-4">
      {legs.map((leg) => (
        <div key={leg.id} className="flex flex-col">
          <StationLeg userId={userId} station={station} leg={leg} />{" "}
        </div>
      ))}
    </div>
  )
}

const Page = ({ params }: { params: { userId: string; crs: string } }) => {
  let { userId, crs } = params
  let router = useRouter()
  let [station, setStation] = useState<TrainStationData | undefined>(undefined)
  useEffect(() => {
    const getStationData = async () => {
      let stationData = await getTrainStationData(parseInt(userId), crs)
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
    <div className="flex flex-col gap-2 w-full">
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
      <StationLegs
        userId={parseInt(userId)}
        station={station}
        legs={station.legs}
      />
    </div>
  )
}

export default Page
