"use client"

import { getLegsForYear } from "@/app/data"
import { Loader } from "@/app/loader"
import { TrainLeg } from "@/app/structs"
import { useState, useEffect } from "react"
import { TotalLegStats, LegList, LegMap } from "../../core"
import { useRouter } from "next/navigation"

const Page = ({ params }: { params: { year: string } }) => {
  let { year } = params
  let router = useRouter()
  const [legs, setLegs] = useState<TrainLeg[] | undefined>(undefined)
  useEffect(() => {
    let yearNumber = parseInt(year)
    if (isNaN(yearNumber)) {
      router.push("/")
    } else {
      const getLegData = async () => {
        let legData = await getLegsForYear(parseInt(year))
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
          <LegList legs={legs} />
        </div>
      )}
    </div>
  )
}

export default Page
