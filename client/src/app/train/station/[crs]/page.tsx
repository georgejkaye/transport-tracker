"use client"

import { getTrainStation } from "@/app/data"
import { Loader } from "@/app/loader"
import { TrainStation } from "@/app/structs"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"

export const Page = ({ params }: { params: { crs: string } }) => {
  let { crs } = params
  let router = useRouter()
  let [station, setStation] = useState<TrainStation | undefined>(undefined)
  useEffect(() => {
    const getStationData = async () => {
      let stationData = await getTrainStation(crs)
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
    <div>
      <h1>{`${station.name} [${station.crs}]`}</h1>
    </div>
  )
}

export default Page
