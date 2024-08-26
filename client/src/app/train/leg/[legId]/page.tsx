"use client"

import { getTrainLeg } from "@/app/data"
import {
  Delay,
  getDelayOrUndefined,
  PlanActTime,
  ShortStationLink,
  StationLink,
} from "@/app/leg"
import { Line } from "@/app/line"
import { Loader } from "@/app/loader"
import {
  dateToLongString,
  dateToTimeString,
  getDurationString,
  getMilesAndChainsString,
  getTrainServiceString,
  maybeDateToTimeString,
  TrainLeg,
  TrainLegCall,
  TrainLegSegment,
  TrainService,
  TrainStockReport,
} from "@/app/structs"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"

const TrainLegService = (props: { service: TrainService }) => {
  let { service } = props
  return (
    <div>
      <div>{getTrainServiceString(service)}</div>
    </div>
  )
}

const TrainLegServices = (props: { services: TrainService[] }) => {
  let { services } = props
  return (
    <div>
      <h2 className="font-bold text-lg mb-2">Services</h2>
      <div className="flex flex-row">
        {services.map((service, i) => (
          <TrainLegService key={i} service={service} />
        ))}
      </div>
    </div>
  )
}

const LegCallRow = (props: { call: TrainLegCall }) => {
  let { call } = props
  let platformString = !call.platform ? "-" : call.platform
  return (
    <div className="flex flex-row gap-2 items-center">
      <div className="w-14 hidden md:block">{call.station.crs}</div>
      <ShortStationLink station={call.station} />
      <div className="w-6 text-center">{platformString}</div>
      <div className="flex flex-col md:flex-row">
        <PlanActTime plan={call.planArr} act={call.actArr} />
        <PlanActTime plan={call.planDep} act={call.actDep} />
      </div>
    </div>
  )
}

const TrainLegStats = (props: { leg: TrainLeg }) => {
  let { leg } = props
  return (
    <div className="flex flex-row gap-2">
      <div>
        {!leg.distance ? (
          ""
        ) : (
          <div>{getMilesAndChainsString(leg.distance)}</div>
        )}
      </div>
      <div>•</div>
      <div>
        {!leg.duration ? "" : <div>{getDurationString(leg.duration)}</div>}
      </div>
    </div>
  )
}

const TrainLegCalls = (props: { calls: TrainLegCall[] }) => {
  let { calls } = props
  return (
    <div>
      <h2 className="text-xl font-bold pb-2">Calls</h2>
      <div className="flex flex-col gap-2">
        {calls.map((call, i) => {
          return (
            <div className="flex flex-col gap-2" key={i}>
              <Line />
              <LegCallRow call={call} />
            </div>
          )
        })}
      </div>
    </div>
  )
}

const TrainStockReportLine = (props: { stock: TrainStockReport }) => {
  let { stock } = props
  let stockDescription = !stock.classNo ? (
    ""
  ) : (
    <Link href={`/train/stock/${stock.classNo}`}>
      {`Class ${stock.classNo}${
        !stock.subclassNo ? "" : `/${stock.subclassNo}`
      }`}
    </Link>
  )
  let stockNumber = !stock.stockNo ? (
    ""
  ) : (
    <Link href={`/train/stock/unit/${stock.stockNo}`}>{stock.stockNo}</Link>
  )
  let stockDescriptionElements = stock.stockNo ? (
    <div className="flex flex-row gap-2">
      {stockNumber}
      {!stock.classNo ? "" : stockDescription}
    </div>
  ) : (
    stockDescription
  )
  let stockCarsText = !stock.cars ? "" : `${stock.cars} cars`
  return (
    <li className="flex flex-row gap-2">
      <div className="">{stockDescriptionElements}</div>
      {stockCarsText === "" ? (
        ""
      ) : (
        <div className="px-1 border">{stockCarsText}</div>
      )}
    </li>
  )
}

const TrainLegStockSegment = (props: { segment: TrainLegSegment }) => {
  let { segment } = props
  return (
    <div>
      <h3 className="font-bold text-lg pb-2">
        {segment.start.name} to {segment.end.name}
      </h3>
      <ul className="flex flex-col gap-2 list-disc">
        {segment.stocks.map((stock, i) => (
          <TrainStockReportLine key={i} stock={stock} />
        ))}
      </ul>
    </div>
  )
}

const TrainLegStockSegments = (props: { segments: TrainLegSegment[] }) => {
  let { segments } = props
  return (
    <div>
      <h2 className="font-bold text-xl pb-2">Rolling stock</h2>
      <div className="flex flex-col gap-4">
        {segments.map((segment, i) => (
          <TrainLegStockSegment segment={segment} key={i} />
        ))}
      </div>
    </div>
  )
}

const Page = ({ params }: { params: { legId: string } }) => {
  let { legId } = params
  let router = useRouter()
  let [leg, setLeg] = useState<TrainLeg | undefined>(undefined)
  useEffect(() => {
    let legIdNumber = parseInt(legId)
    if (isNaN(legIdNumber)) {
      router.push("/")
    } else {
      const getLegData = async () => {
        let legData = await getTrainLeg(legIdNumber)
        if (!legData) {
          router.push("/")
        } else {
          setLeg(legData)
        }
      }
      getLegData()
    }
  }, [])
  return !leg ? (
    <Loader />
  ) : (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold">
        {`${leg.calls[0].station.name} to ${
          leg.calls[leg.calls.length - 1].station.name
        }`}
      </h1>
      <div className="text-xl">{dateToLongString(leg.start)}</div>
      <Line />
      <TrainLegStats leg={leg} />
      <Line />
      <TrainLegServices services={leg.services} />
      <Line />
      <TrainLegStockSegments segments={leg.stock} />
      <Line />
      <TrainLegCalls calls={leg.calls} />
    </div>
  )
}

export default Page
