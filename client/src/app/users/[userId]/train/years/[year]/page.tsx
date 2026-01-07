"use client"

import { Loader } from "@/app/loader"
import { LegMap } from "../map"
import { notFound, useRouter } from "next/navigation"
import client from "@/app/api/client"
import { isNumber } from "@/app/utils/number"
import TotalStatsPane from "./TotalStatsPane"
import DistanceStatsPane from "./DistanceStatsPane"

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
  const {
    data: geometries,
    error: geometriesError,
    isLoading: isLoadingGeometries,
  } = client.useQuery(
    "get",
    "/users/{user_id}/train/legs/geometries/years/{year}",
    {
      params: {
        path: {
          user_id: userId,
          year: year,
        },
      },
    }
  )
  return (
    <div className="flex flex-col gap-4">
      <h1 className="font-bold text-3xl my-2">
        Train journey stats for {year}
      </h1>
      {isLoadingStats || !stats ? (
        <Loader />
      ) : (
        <div>
          <TotalStatsPane
            count={stats.leg_count}
            totalDistance={stats.total_distance}
            totalDuration={stats.total_duration}
            totalDelay={stats.total_delay}
          />
          <DistanceStatsPane
            longestDistanceLegs={stats.longest_distance_legs}
            shortestDistanceLegs={stats.shortest_distance_legs}
          />
          {isLoadingGeometries || !geometries ? (
            <Loader />
          ) : (
            <LegMap legs={geometries} />
          )}
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
