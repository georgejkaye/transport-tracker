import axios, { AxiosError } from "axios"
import {
  responseToLeg,
  responseToTrainStation,
  responseToTrainStationData,
  TrainLeg,
  TrainStation,
  TrainStationData,
} from "./structs"

export const getLegs = async (): Promise<TrainLeg[]> => {
  let endpoint = "/api/train/legs"
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
  legId: number
): Promise<TrainLeg | undefined> => {
  let endpoint = `/api/train/leg/${legId}`
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
  let endpoint = `/api/train/station/${stationCrs}`
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
