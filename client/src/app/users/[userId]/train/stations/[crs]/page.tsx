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
import { useEffect, useState, use } from "react"
import { Delay, delayWidth, LegIconLink, PlanActTime } from "@/app/leg"
import { linkStyle } from "@/app/styles"
import Link from "next/link"
import {
  TransportUserTrainStationLegOutData,
  TransportUserTrainStationOutData,
} from "@/app/utils/train"
import client from "@/app/api/client"

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
  leg: TransportUserTrainStationLegOutData
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
      <LegIconLink userId={userId} legId={leg.leg_id} />
      <div className="flex flex-col md:flex-row flex-1">
        <div>
          <div className="flex flex-row gap-2 items-center pb-2">
            <div className="w-28 text-left flex-1">
              {!leg.plan_arr
                ? null
                : dateToShortString(new Date(Date.parse(leg.plan_arr)))}
            </div>
            {!leg.act_arr ? (
              ""
            ) : (
              <div>{`${dateToTimeString(new Date(Date.parse(leg.act_arr)))}`}</div>
            )}
            {!leg.act_dep ? (
              ""
            ) : (
              <div>{`${dateToTimeString(new Date(Date.parse(leg.act_dep)))}`}</div>
            )}
          </div>
          <div className="flex flex-col md:flex-row w-full">
            <div className="flex flex-row gap-1">
              <Link
                className={`${originStyle} ${linkStyle}`}
                href={`/users/${userId}/train/station/${leg.board_station.station_crs}`}
              >
                {leg.board_station.station_name}
              </Link>
              <div>to</div>
              <Link
                className={`${destinationStyle} ${linkStyle}`}
                href={`/users/${userId}/train/station/${leg.alight_station.station_crs}`}
              >
                {leg.alight_station.station_name}
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
      <LegIconLink userId={userId} legId={leg.leg_id} />
      <div className="w-28">
        {!leg.act_arr
          ? ""
          : dateToShortString(new Date(Date.parse(leg.act_arr)))}
      </div>
      <Link
        className={`${originStyle} ${linkStyle}`}
        href={`/users/${userId}/train/station/${leg.board_station.station_crs}`}
      >
        {leg.board_station.station_name}
      </Link>
      <PlanActTime
        plan={!leg.plan_arr ? null : new Date(Date.parse(leg.plan_arr))}
        act={!leg.act_arr ? null : new Date(Date.parse(leg.act_arr))}
      />
      <Link
        className={`${destinationStyle} ${linkStyle}`}
        href={`/users/${userId}/train/station/${leg.alight_station.station_crs}`}
      >
        {leg.board_station.station_name}
      </Link>
      <PlanActTime
        plan={!leg.plan_dep ? null : new Date(Date.parse(leg.plan_dep))}
        act={!leg.act_dep ? null : new Date(Date.parse(leg.act_dep))}
      />
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
  station: TransportUserTrainStationOutData
  leg: TransportUserTrainStationLegOutData
}) => {
  let { userId, station, leg } = props
  let boardsAtThisStation =
    leg.board_station.station_crs === station.station_crs
  let alightsAtThisStation =
    leg.alight_station.station_crs === station.station_crs
  let operatorText = leg.brand
    ? leg.brand.operator_name
    : leg.operator.operator_name
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
          operatorBg={"#000000"}
          operatorFg={"#fffffff"}
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
          operatorBg={"#000000"}
          operatorFg={"#fffffff"}
          passStyle={passStyle}
        />
      </div>
    </div>
  )
}

const StationLegs = (props: {
  userId: number
  station: TransportUserTrainStationOutData
  legs: TransportUserTrainStationLegOutData[]
}) => {
  let { userId, station, legs } = props
  return (
    <div className="flex flex-col gap-4">
      {legs.map((leg) => (
        <div key={leg.leg_id} className="flex flex-col">
          <StationLeg userId={userId} station={station} leg={leg} />{" "}
        </div>
      ))}
    </div>
  )
}

const Page = (props: { params: Promise<{ userId: string; crs: string }> }) => {
  const params = use(props.params)
  let { userId, crs } = params
  let router = useRouter()
  const { data: station } = client.useQuery(
    "get",
    "/users/{user_id}/train/stations/crs/{station_crs}",
    {
      params: {
        path: {
          user_id: parseInt(userId),
          station_crs: crs,
        },
      },
    },
  )
  return !station ? (
    <Loader />
  ) : (
    <div className="flex flex-col gap-2 w-full">
      <div className="px-4">
        <h1 className="text-3xl font-bold flex gap-2">
          <span className="text-gray-700">{station.station_crs}</span>
          <span>{station.station_name}</span>
        </h1>
        <div>
          {station.station_brand
            ? station.station_brand.operator_name
            : station.station_operator.operator_name}
        </div>
      </div>
      <StationLegs
        userId={parseInt(userId)}
        station={station}
        legs={station.station_legs}
      />
    </div>
  )
}

export default Page
