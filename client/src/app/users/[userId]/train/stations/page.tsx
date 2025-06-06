"use client"

import { getTrainStations } from "@/app/data"
import { Line } from "@/app/line"
import { Loader } from "@/app/loader"
import { TrainStationData } from "@/app/structs"
import { linkStyle } from "@/app/styles"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"

const StationCallStat = (props: { name: string; stat: number }) => {
  let { name, stat } = props
  return (
    <div className="flex flex-row gap-2 items-center">
      <div className="text-xs">{name}</div>
      <div className="w-6 text-center">{stat}</div>
    </div>
  )
}

const StationRow = (props: { userId: number; station: TrainStationData }) => {
  let { userId, station } = props
  return (
    <div className="flex flex-col lg:flex-row gap-2 lg:items-center">
      <div className="flex flex-row gap-2">
        <div className="">{station.crs}</div>
        <Link href={`/users/${userId}/train/stations/${station.crs}`}>
          <div className={`${linkStyle}`}>{station.name}</div>
        </Link>
      </div>
      <div className="text-sm lg:flex-1">{station.operator.name}</div>
      <div className="flex flex-row gap-2">
        <StationCallStat name="Starts" stat={station.starts} />
        <StationCallStat name="Ends" stat={station.finishes} />
        <StationCallStat name="Passes" stat={station.intermediates} />
      </div>
    </div>
  )
}

const Page = ({ params }: { params: { userId: string } }) => {
  let [stations, setStations] = useState<TrainStationData[] | undefined>(
    undefined
  )
  let { userId } = params
  let userIdNumber = parseInt(userId)
  let router = useRouter()
  useEffect(() => {
    if (isNaN(userIdNumber)) {
      router.push("/")
    }
    const getStationData = async () => {
      let stationData = await getTrainStations(userIdNumber)
      if (stationData) {
        setStations(stationData)
      }
    }
    getStationData()
  }, [])
  return !stations ? (
    <Loader />
  ) : (
    <div>
      <h1 className="text-2xl font-bold mb-2">Railway stations</h1>
      <div className="flex flex-col gap-2">
        {stations.map((station) => (
          <div key={station.crs} className="flex flex-col gap-2">
            <Line />
            <StationRow userId={userIdNumber} station={station} />
          </div>
        ))}
      </div>
    </div>
  )
}

export default Page
