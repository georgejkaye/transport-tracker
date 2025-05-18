"use client"

import { getLegsForYear, getStatsForYear } from "@/app/data"
import { Loader } from "@/app/loader"
import { Stats, TrainLeg } from "@/app/structs"
import { useState, useEffect } from "react"
import {
  ClassStats,
  GeneralStats,
  LegStats,
  OperatorStats,
  StationStats,
  UnitStats,
} from "../core"
import { LegMap } from "../map"
import { useRouter } from "next/navigation"

const Page = ({ params }: { params: { userId: string; year: string } }) => {
  let { userId, year } = params
  let router = useRouter()
  const [validYear, setValidYear] = useState(false)
  const [stats, setStats] = useState<Stats | undefined>(undefined)
  const [legs, setLegs] = useState<TrainLeg[] | undefined>(undefined)
  useEffect(() => {
    let yearNumber = parseInt(year)
    let userIdNumber = parseInt(userId)
    if (isNaN(yearNumber) || isNaN(userIdNumber)) {
      router.push("/")
    } else {
      setValidYear(true)
      const getLegData = async () => {
        let stats = await getStatsForYear(userIdNumber, yearNumber)
        let legs = await getLegsForYear(userIdNumber, yearNumber)
        setStats(stats)
        setLegs(legs)
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
                <LegStats stats={stats.legStats} />
                <StationStats stats={stats.stationStats} />
                <OperatorStats stats={stats.operatorStats} />
                {stats.classStats.length > 0 && (
                  <div className="flex flex-row gap-4">
                    <ClassStats stats={stats.classStats} />
                    {stats.unitStats.length > 0 && (
                      <UnitStats stats={stats.unitStats} />
                    )}
                  </div>
                )}
                {legs === undefined ? (
                  <Loader />
                ) : (
                  <div>
                    <LegMap legs={legs} />
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
