"use client"

import { getTrainLeg } from "@/app/data"
import { Delay, getDelayOrUndefined, StationLink } from "@/app/leg"
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
      <div className="flex flex-row">
        {services.map((service, i) => (
          <TrainLegService key={i} service={service} />
        ))}
      </div>
    </div>
  )
}

const PlanActTime = (props: { plan?: Date; act?: Date }) => {
  let { plan, act } = props
  let { delay, text } = getDelayOrUndefined(plan, act)
  return (
    <div className="flex flex-row">
      <div className="w-14 text-center">{maybeDateToTimeString(plan)}</div>
      <div className="w-14 text-center font-bold">
        {maybeDateToTimeString(act)}
      </div>
      <Delay plan={plan} act={act} />
    </div>
  )
}

const LegCallRow = (props: { call: TrainLegCall }) => {
  let { call } = props
  let platformString = !call.platform ? "-" : call.platform
  return (
    <div className="flex flex-row gap-2 items-center">
      <div className="w-12">{call.station.crs}</div>
      <StationLink station={call.station} />
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
    <div className="flex flex-col gap-2">
      <div>
        {!leg.distance ? (
          ""
        ) : (
          <div>{getMilesAndChainsString(leg.distance)}</div>
        )}
      </div>
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
      <h2>Calls</h2>

      <div className="flex flex-col gap-2">
        {calls.map((call, i) => {
          return (
            <div className="flex flex-col gap-2" key={i}>
              <hr className="h-px border-0 bg-gray-600" />
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
    <Link href={`trains/stock/${stock.classNo}`}>
      {`Class ${stock.classNo}${
        !stock.subclassNo ? "" : `/${stock.subclassNo}`
      }`}
    </Link>
  )
  let stockNumber = !stock.stockNo ? (
    ""
  ) : (
    <Link href={`trains/stock/unit/${stock.stockNo}`}>{stock.stockNo}</Link>
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
    <div className="flex flex-row gap-2">
      <div className="">{stockDescriptionElements}</div>
      {stockCarsText === "" ? (
        ""
      ) : (
        <div className="px-1 border">{stockCarsText}</div>
      )}
    </div>
  )
}

const TrainLegStockSegment = (props: { segment: TrainLegSegment }) => {
  let { segment } = props
  return (
    <div>
      <div>
        {segment.start.name} to {segment.end.name}
      </div>
      <div className="flex flex-col gap-2">
        {segment.stocks.map((stock, i) => (
          <TrainStockReportLine key={i} stock={stock} />
        ))}
      </div>
    </div>
  )
}

const TrainLegStockSegments = (props: { segments: TrainLegSegment[] }) => {
  let { segments } = props
  return (
    <div>
      <h2>Rolling stock</h2>
      <div className="flex flex-row">
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
      <h1 className="text-xl font-bold">
        {`${leg.calls[0].station.name} to ${
          leg.calls[leg.calls.length - 1].station.name
        }`}
      </h1>
      <div>{dateToLongString(leg.start)}</div>
      <TrainLegServices services={leg.services} />
      <TrainLegStats leg={leg} />
      <TrainLegStockSegments segments={leg.stock} />
      <TrainLegCalls calls={leg.calls} />
    </div>
  )
}

export default Page
