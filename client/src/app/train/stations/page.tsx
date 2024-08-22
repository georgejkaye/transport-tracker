"use client"

import { getTrainStations } from "@/app/data"
import { Loader } from "@/app/loader"
import { TrainStationData } from "@/app/structs"
import Image from "next/image"
import { useEffect, useState } from "react"

const StationRow = (props: { station: TrainStationData }) => {
  let { station } = props
  return (
    <div>
      {station.name} {station.operator.name} {station.starts} {station.finishes}{" "}
      {station.intermediates}
      {!station.img ? (
        ""
      ) : (
        <Image
          src={station.img}
          alt={`Station sign for ${station.name}`}
          width={300}
          height={200}
        />
      )}
    </div>
  )
}

const Page = () => {
  let [stations, setStations] = useState<TrainStationData[] | undefined>(
    undefined
  )
  useEffect(() => {
    const getStationData = async () => {
      let stationData = await getTrainStations()
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
      {stations.map((station, i) => (
        <div key={i}>
          <StationRow station={station} />
        </div>
      ))}
    </div>
  )
}

export default Page
