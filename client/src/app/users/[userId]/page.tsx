"use client"
import { use } from "react"

import Link from "next/link"
import client from "@/app/api/client"
import { isNumber } from "@/app/utils/number"
import { notFound } from "next/navigation"
import { Loader } from "@/app/loader"
import UserHeader from "./components/UserHeader"
import LegFeed from "./components/LegFeed"
import StatsPane from "./components/StatsPane"
import StatsGraphs from "./train/years/[year]/StatsGraphs"

interface ContentProps {
  userId: number
}

const Content = ({ userId }: ContentProps) => {
  const {
    data: user,
    error,
    isLoading: isLoadingUser,
  } = client.useQuery("get", "/users/{user_id}", {
    params: {
      path: {
        user_id: userId,
      },
    },
  })
  return isLoadingUser || user == undefined ? (
    <Loader />
  ) : (
    <div className="flex flex-col gap-4">
      <UserHeader
        trainStats={user.train_stats}
        userName={user.user_name}
        displayName={user.display_name}
      />
      <StatsGraphs
        trainLegStats={user.train_stats.leg_stats_yearly}
        trainOperatorStats={user.train_stats.operator_stats_yearly}
        trainStationStats={user.train_stats.station_stats_yearly}
      />
      <div className="flex flex-row gap-4">
        <div className="flex-1">
          <LegFeed userId={user.user_id} />
        </div>
        <div className="hidden md:block flex flex-row w-1/5">
          <StatsPane trainStats={user.train_stats} />
        </div>
      </div>
    </div>
  )
}

const Page = (props: { params: Promise<{ userId: string }> }) => {
  let { userId } = use(props.params)
  return !isNumber(userId) ? notFound() : <Content userId={Number(userId)} />
}

export default Page
