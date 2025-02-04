import axios from "axios"
import {
  responseToLeg,
  responseToTrainStationData,
  TrainLeg,
  TrainStationData,
} from "./structs"

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

export const getLegsForYear = async (year: number): Promise<TrainLeg[]> => {
  let yearString = getYearString(year)
  let endpoint = `/api/train/legs/years/${yearString}?fetch_geometries=true`
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

export const getStatsForYear = async (year: number): Promise<TrainLeg[]> => {
  let yearString = getYearString(year)
  let endpoint = `/api/train/legs/year/${yearString}?fetch_geometries=true`
  try {
    let response = await axios.get(endpoint)
    let data = response.data
    let legs = data.map(responseToStats)
    return legs
  } catch (e) {
    console.log(e)
    return []
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
