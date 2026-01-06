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
import { notFound, useRouter } from "next/navigation"
import client from "@/app/api/client"
import { isNumber } from "@/app/utils/number"
import TotalStatsPane from "./TotalStatsPane"

interface ContentProps {
  userId: number
  year: number
}

const Content = ({ userId, year }: ContentProps) => {
  const {
    data: stats,
    error,
    isLoading: isLoadingStats,
  } = client.useQuery("get", "/users/{user_id}/train/stats/years/{year}", {
    params: {
      path: {
        user_id: userId,
        year: year,
      },
    },
  })
  return (
    <div className="flex flex-col gap-4">
      <h1 className="font-bold text-3xl my-2">
        Train journey stats for {year}
      </h1>
      {isLoadingStats ? (
        <Loader />
      ) : (
        <div>
          <TotalStatsPane
            count={stats?.leg_count ?? 0}
            totalDistance={stats?.total_distance ?? 0}
            totalDuration={stats?.total_duration ?? 0}
            totalDelay={stats?.total_delay ?? 0}
          />
        </div>
      )}
    </div>
  )
}

const Page = ({ params }: { params: { userId: string; year: string } }) => {
  let { userId, year } = params
  return !isNumber(userId) || !isNumber(year) ? (
    notFound()
  ) : (
    <Content userId={Number(userId)} year={Number(year)} />
  )
}

export default Page
