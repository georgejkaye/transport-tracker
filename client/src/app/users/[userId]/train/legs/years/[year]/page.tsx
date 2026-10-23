"use client"

import { Loader } from "@/app/loader"
import { TotalLegStats, LegList, LegMap } from "../../core"
import client from "@/app/api/client"
import { use } from "react"

const Page = (props: { params: Promise<{ userId: string; year: string }> }) => {
  const params = use(props.params)
  let { userId, year } = params
  const { data: legs } = client.useQuery(
    "get",
    "/users/{user_id}/train/legs/years/{year}",
    { params: { path: { user_id: parseInt(userId), year: parseInt(year) } } },
  )

  return (
    <div>
      {legs === undefined ? (
        <Loader />
      ) : (
        <div className="flex flex-col gap-4">
          <TotalLegStats legs={legs.items ?? []} />
          <LegMap userId={parseInt(userId)} />
          <LegList userId={parseInt(userId)} legs={legs.items ?? []} />
        </div>
      )}
    </div>
  )
}

export default Page
