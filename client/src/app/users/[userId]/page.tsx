"use client"

import { FaBusSimple, FaTrain } from "react-icons/fa6"
import {
  AttributionControl,
  Layer,
  LineLayer,
  LngLatBoundsLike,
  Map,
  Source,
  ViewState,
} from "react-map-gl/maplibre"
import Link from "next/link"
import client from "@/app/api/client"
import { isNumber } from "@/app/utils/number"
import { notFound } from "next/navigation"
import { Loader } from "@/app/loader"
import { TransportUserTrainLegOutData } from "@/app/utils/train"
import { getMilesAndChainsString } from "@/app/utils/distance"
import { getDurationString } from "@/app/utils/duration"
import { Duration } from "js-joda"
import { getDelayString } from "@/app/utils/delay"
import { getLongDateAndTime } from "@/app/utils/datetime"
import {
  getBoundingBoxForFeatureCollection,
  getFeatureCollection,
} from "@/app/utils/map"
import { useEffect, useState } from "react"

const YearLink = (props: { userId: number; year: number }) => (
  <Link
    className="cursor-pointer"
    href={`/users/${props.userId}/train/legs/years/${props.year}`}
  >
    <div className="p-4 text-xl rounded bg-blue-400">{props.year}</div>
  </Link>
)

interface UserHeaderProps {
  userId: number
  userName: string
  displayName: string
}

const UserHeader = ({ userId, userName, displayName }: UserHeaderProps) => {
  const { data, isLoading, error } = client.useQuery(
    "get",
    "/users/{user_id}",
    { params: { path: { user_id: userId } } },
  )
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-bold">{displayName}</h1>
        <div>@{userName}</div>
      </div>
      <div className="flex flex-row gap-4 items-center">
        <FaTrain />
        <div>{data?.train_stats.leg_stats_overall?.count}</div>
        <div>
          {getMilesAndChainsString(
            Number(data?.train_stats.leg_stats_overall?.total_distance),
          )}
        </div>
        {data?.train_stats.leg_stats_overall?.total_duration && (
          <div>
            {getDurationString(
              Duration.parse(
                data?.train_stats.leg_stats_overall?.total_duration,
              ),
            )}
          </div>
        )}
        <FaBusSimple />
        <div>-</div>
      </div>
    </div>
  )
}

interface LegFeedItemMapProps {
  leg: TransportUserTrainLegOutData
}

const lineLayer: LineLayer = {
  id: "line",
  source: "geometry",
  type: "line",
  paint: {
    "line-width": 5,
    "line-color": ["get", "color"],
  },
  layout: {
    "line-cap": "round",
  },
}

const boundingBoxPadding = 0.1

const LegFeedItemMap = ({ leg }: LegFeedItemMapProps) => {
  let { data, isLoading, error } = client.useQuery(
    "get",
    "/train/legs/geometries/{leg_id}",
    {
      params: {
        path: {
          leg_id: leg.leg_id,
        },
      },
    },
  )
  let featureCollection = data?.geometry
    ? getFeatureCollection(data?.geometry, "#0c0040")
    : undefined
  let bounds = featureCollection
    ? getBoundingBoxForFeatureCollection(featureCollection)
    : undefined

  let windowWidth = window.innerWidth
  let width = windowWidth < 1024 ? "calc(100vw - 60px)" : "1000"
  let viewState = bounds && {
    bounds: [
      bounds.minLng - boundingBoxPadding,
      bounds.minLat - boundingBoxPadding,
      bounds.maxLng + boundingBoxPadding,
      bounds.maxLat + boundingBoxPadding,
    ],
  }

  return isLoading ? (
    <Loader />
  ) : (
    <div className="overflow-hidden">
      {viewState && (
        <Map
          attributionControl={false}
          interactive={false}
          style={{ height: 400, width }}
          {...viewState}
          mapStyle={"https://tiles.openfreemap.org/styles/bright"}
        >
          <Source id="lines" type="geojson" data={featureCollection}>
            <Layer {...lineLayer} />
          </Source>
          <AttributionControl compact={true} />
        </Map>
      )}
    </div>
  )
}

interface LegFeedItemProps {
  leg: TransportUserTrainLegOutData
}

const LegFeedItem = ({ leg }: LegFeedItemProps) => {
  return (
    <div className="shadow-lg p-4 flex flex-col gap-2">
      <div className="text-sm text-gray-600">
        {getLongDateAndTime(leg.start_datetime)}
      </div>
      <div className="font-bold text-xl flex flex-row gap-2 items-center">
        <FaTrain />
        {leg.board_station.station_name} to {leg.alight_station.station_name}
      </div>
      <div className="flex flex-row gap-4">
        <div>{leg.operator.operator_code}</div>
        <div>
          {leg.distance && getMilesAndChainsString(parseFloat(leg.distance))}
        </div>
        <div>
          {leg.duration && getDurationString(Duration.parse(leg.duration))}{" "}
        </div>
        {leg.delay !== null && leg.delay !== 0 && (
          <div>{getDelayString(leg.delay)} </div>
        )}
      </div>
      <LegFeedItemMap leg={leg} />
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
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-2">
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
    <div className="flex flex-col gap-4">
      <UserHeader
        userId={user.user_id}
        userName={user.user_name}
        displayName={user.display_name}
      />
      <LegFeed userId={user.user_id} />
    </div>
  )
}

const Page = ({ params }: { params: { userId: string } }) => {
  let { userId } = params
  return !isNumber(userId) ? notFound() : <Content userId={Number(userId)} />
}

export default Page
