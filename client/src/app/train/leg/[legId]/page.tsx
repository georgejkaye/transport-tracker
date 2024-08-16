"use client"

import { getTrainLeg } from "@/app/data"
import { Loader } from "@/app/loader"
import { TrainLeg } from "@/app/structs"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"

export const Page = ({ params }: { params: { legId: string } }) => {
  let { legId } = params
  let router = useRouter()
  let [leg, setLeg] = useState<TrainLeg | undefined>(undefined)
  useEffect(() => {
    console.log("leg", legId)
    let legIdNumber = parseInt(legId)
    console.log("legnumber", legIdNumber)
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
    <div>
      <h1>
        {`${leg.calls[0].station.name} to ${
          leg.calls[leg.calls.length - 2].station.name
        }`}
      </h1>
    </div>
  )
}

export default Page
