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

export const getLegs = async (userId: number): Promise<TrainLeg[]> => {
  let endpoint = `/api/users/${userId}/train/legs/`
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
  userId: number,
  year: number
): Promise<TrainLeg[]> => {
  let yearString = year.toString().padStart(4, "0")
  let endpoint = `/api/users/${userId}/train/legs/years/${yearString}?fetch_geometries=true`
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

export const getStatsForYear = async (
  userId: number,
  year: number
): Promise<Stats | undefined> => {
  let yearString = getYearString(year)
  let endpoint = `/api/users/${userId}/train/stats/years/${yearString}?fetch_geometries=false`
  try {
    let response = await axios.get(endpoint)
    let data = response.data
    console.log(data)
    let stats = responseToStats(data)
    return stats
  } catch (e) {
    console.error(e)
    return undefined
  }
}

export const getTrainLeg = async (
  userId: number,
  legId: number
): Promise<TrainLeg | undefined> => {
  let endpoint = `/api/users/${userId}/train/legs/${legId}?fetch_geometries=true`
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
  userId: number,
  stationCrs: string
): Promise<TrainStationData | undefined> => {
  let endpoint = `/api/users/${userId}/train/stations/${stationCrs}`
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

export const getTrainStations = async (
  userId: number
): Promise<TrainStationData[] | undefined> => {
  let endpoint = `/api/users/${userId}/train/stations`
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
