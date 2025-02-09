import axios from "axios"
import {
  responseToLeg,
  responseToStats,
  responseToTrainStationData,
  Stats,
  TrainLeg,
  TrainStationData,
} from "./structs"
import { Dispatch, SetStateAction } from "react"

const getYearString = (year: number) => year.toString().padStart(4, "0")

export const getLegs = async (): Promise<TrainLeg[]> => {
  let endpoint = "/api/train/legs/"
  try {
    let response = await axios.get(endpoint)
    let data = response.data
    let legs = data.map(responseToLeg)
    return legs
  } catch (e) {
    console.log(e)
    return []
  }
}

export const getLegsForYear = async (
  year: number,
  setLegs: Dispatch<SetStateAction<TrainLeg[] | undefined>>
): Promise<void> => {
  let yearString = getYearString(year)
  let endpoint = `/api/train/legs/years/${yearString}?fetch_geometries=true`
  try {
    let response = await axios.get(endpoint)
    let data = response.data
    let legs = data.map(responseToLeg)
    setLegs(legs)
    return legs
  } catch (e) {
    console.log(e)
  }
}

export const getStatsForYear = async (
  year: number,
  setStats: Dispatch<SetStateAction<Stats | undefined>>
): Promise<void> => {
  let yearString = getYearString(year)
  let endpoint = `/api/train/stats/years/${yearString}?fetch_geometries=false`
  try {
    let response = await axios.get(endpoint)
    let data = response.data
    let stats = responseToStats(data)
    setStats(stats)
  } catch (e) {
    console.log(e)
  }
}

export const getTrainLeg = async (
  legId: number
): Promise<TrainLeg | undefined> => {
  let endpoint = `/api/train/legs/${legId}?fetch_geometries=true`
  try {
    let response = await axios.get(endpoint)
    let data = response.data
    let leg = responseToLeg(data)
    return leg
  } catch (e) {
    console.log(e)
    return undefined
  }
}

export const getTrainStationData = async (
  stationCrs: string
): Promise<TrainStationData | undefined> => {
  let endpoint = `/api/train/stations/${stationCrs}`
  try {
    let response = await axios.get(endpoint)
    let data = response.data
    let station = responseToTrainStationData(data)
    return station
  } catch (e) {
    console.log(e)
    return undefined
  }
}

export const getTrainStations = async (): Promise<
  TrainStationData[] | undefined
> => {
  let endpoint = `/api/train/stations`
  try {
    let response = await axios.get(endpoint)
    let data = response.data
    let stations = data.map(responseToTrainStationData)
    return stations
  } catch (e) {
    console.log(e)
    return undefined
  }
}
