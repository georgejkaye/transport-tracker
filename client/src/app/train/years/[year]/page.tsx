"use client"

import { getLegsForYear, getStatsForYear } from "@/app/data"
import { Loader } from "@/app/loader"
import { Stats, TrainLeg } from "@/app/structs"
import { useState, useEffect } from "react"
import {
  LegList,
  GeneralStats,
  StationStats,
  OperatorStats,
  ClassStats,
  UnitStats,
} from "@/app/train/years/core"
import { useRouter } from "next/navigation"
import { LegMap } from "@/app/train/years/map"

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
