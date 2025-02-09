"use client"

import { getLegsForYear, getStatsForYear } from "@/app/data"
import { Loader } from "@/app/loader"
import { Stats, TrainLeg } from "@/app/structs"
import { useState, useEffect } from "react"
import {
  LegList,
  LegMap,
  GeneralStats,
  StationStats,
  OperatorStats,
} from "@/app/train/years/core"
import { useRouter } from "next/navigation"

const Page = ({ params }: { params: { year: string } }) => {
  let { year } = params
  let router = useRouter()
  const [validYear, setValidYear] = useState(false)
  const [stats, setStats] = useState<Stats | undefined>(undefined)
  const [legs, setLegs] = useState<TrainLeg[] | undefined>(undefined)
  useEffect(() => {
    let yearNumber = parseInt(year)
    if (isNaN(yearNumber)) {
      router.push("/")
    } else {
      setValidYear(true)
      const getLegData = async () => {
        getStatsForYear(yearNumber, setStats)
        getLegsForYear(yearNumber, setLegs)
      }
      getLegData()
    }
  }, [])
  return (
    <div>
      {!validYear ? (
        <Loader />
      ) : (
        <div>
          <h1 className="font-bold text-3xl my-2">
            Train journey stats for {year}
          </h1>
          <div>
            {stats === undefined ? (
              <Loader />
            ) : (
              <div className="flex flex-col gap-4">
                <GeneralStats stats={stats} />
                <StationStats stats={stats.stationStats} />
                <OperatorStats stats={stats.operatorStats} />
                {legs === undefined ? (
                  <Loader />
                ) : (
                  <div>
                    <LegMap legs={legs} />
                    <LegList legs={legs} />
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default Page
