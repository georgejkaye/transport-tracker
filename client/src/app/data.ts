import axios from "axios"
import {
  responseToLeg,
  responseToTrainStationData,
  TrainLeg,
  TrainStationData,
} from "./structs"

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
  let endpoint = `/api/users/${userId}/train/legs/year/${yearString}?fetch_geometries=true`
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
