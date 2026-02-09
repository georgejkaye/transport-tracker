"use client"

import Link from "next/link"
import { linkStyle } from "../../styles"
import client from "@/app/api/client"
import { isNumber } from "@/app/utils/number"
import { notFound } from "next/navigation"
import { Loader } from "@/app/loader"
import { TransportUserTrainLegOutData } from "@/app/utils/train"

const YearLink = (props: { userId: number; year: number }) => (
  <Link
    className="cursor-pointer"
    href={`/users/${props.userId}/train/legs/years/${props.year}`}
  >
    <div className="p-4 text-xl rounded bg-blue-400">{props.year}</div>
  </Link>
)

interface UserHeaderProps {
  userName: string
  displayName: string
}

const UserHeader = ({ userName, displayName }: UserHeaderProps) => {
  return (
    <div className="flex flex-col gap-1">
      <h1 className="text-3xl font-bold">{displayName}</h1>
      <div>@{userName}</div>
    </div>
  )
}

interface LegFeedItemProps {
  leg: TransportUserTrainLegOutData
}

const LegFeedItem = ({ leg }: LegFeedItemProps) => {
  return (
    <div>
      {leg.board_station.station_name} to {leg.alight_station.station_name}
    </div>
  )
}

interface LegFeedProps {
  userId: number
}

const LegFeed = ({ userId }: LegFeedProps) => {
  const { data, fetchNextPage, hasNextPage, isFetching } =
    client.useInfiniteQuery(
      "get",
      "/users/{user_id}/train/legs",
      {
        params: {
          path: {
            user_id: userId,
          },
        },
      },
      {
        pageParamName: "page_no",
        getNextPageParam: (lastPage) => `${lastPage.current_page + 1}`,
        initialPageParam: 0,
      },
    )
  return isFetching ? (
    <Loader />
  ) : (
    <div>
      <div>
        {data?.pages.map((page) => (
          <>
            {page.items.map((leg) => (
              <LegFeedItem leg={leg} key={leg.leg_id} />
            ))}
          </>
        ))}
      </div>
      {hasNextPage && (
        <button onClick={() => fetchNextPage()} disabled={isFetching}>
          {isFetching ? "Loading..." : "Load more"}
        </button>
      )}
    </div>
  )
}

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
    <div>
      <UserHeader userName={user.user_name} displayName={user.display_name} />
      <LegFeed userId={user.user_id} />
    </div>
  )
}

const Page = ({ params }: { params: { userId: string } }) => {
  let { userId } = params
  return !isNumber(userId) ? notFound() : <Content userId={Number(userId)} />
}

export default Page
