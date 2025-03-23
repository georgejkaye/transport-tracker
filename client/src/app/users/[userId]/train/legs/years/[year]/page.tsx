"use client"

import { getLegsForYear } from "@/app/data"
import { Loader } from "@/app/loader"
import { TrainLeg } from "@/app/structs"
import { useState, useEffect } from "react"
import { TotalLegStats, LegList, LegMap } from "../../core"
import { useRouter } from "next/navigation"

const Page = ({ params }: { params: { userId: string; year: string } }) => {
  let { userId, year } = params
  let userIdNumber = parseInt(userId)
  let yearNumber = parseInt(year)
  let router = useRouter()
  const [legs, setLegs] = useState<TrainLeg[] | undefined>(undefined)
  useEffect(() => {
    let yearNumber = parseInt(year)
    if (isNaN(yearNumber) || isNaN(userIdNumber)) {
      router.push("/")
    } else {
      const getLegData = async () => {
        let legData = await getLegsForYear(userIdNumber, yearNumber)
        setLegs(legData)
      }
      getLegData()
    }
  }, [])
  return (
    <div>
      {legs === undefined ? (
        <Loader />
      ) : (
        <div className="flex flex-col gap-4">
          <TotalLegStats legs={legs} />
          <LegMap legs={legs} />
          <LegList userId={userIdNumber} legs={legs} />
        </div>
      )}
    </div>
  )
}

export default Page
