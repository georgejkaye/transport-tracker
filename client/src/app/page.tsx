"use client"

import { useEffect, useState } from "react"
import {
  dateToShortString,
  getLegDestination,
  getLegOrigin,
  getMilesAndChainsString,
  TrainLeg,
  getDurationString,
  getMaybeDurationString,
} from "./structs"
import { getLegs } from "./data"
import { EndpointSection, LegIconLink, TotalStat } from "./leg"
import { Loader } from "./loader"

const Page = () => {
  return <div></div>
}

export default Page
