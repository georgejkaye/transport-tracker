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
        trainStats={user.train_stats.overall_stats}
        userName={user.user_name}
        displayName={user.display_name}
      />
      <hr className="border-1 border-blue-700" />
      <StatsGraphs trainStats={user.train_stats.year_stats} />
      <hr className="border-1 border-blue-700" />
      <div className="flex flex-row gap-4">
        <div className="hidden md:block flex-1">
          <LegFeed userId={user.user_id} />
        </div>
        <StatsPane trainStats={user.train_stats} />
      </div>
    </div>
  )
}

const Page = (props: { params: Promise<{ userId: string }> }) => {
  let { userId } = use(props.params)
  return !isNumber(userId) ? notFound() : <Content userId={Number(userId)} />
}

export default Page
