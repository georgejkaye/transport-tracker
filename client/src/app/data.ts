import axios, { AxiosError } from "axios"
import { responseToLeg, TrainLeg } from "./structs"

export const getLegs = async (): Promise<TrainLeg[]> => {
  let endpoint = "/api/legs"
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

export const getLeg = async (legId: number): Promise<TrainLeg | undefined> => {
  let endpoint = "/api/leg"
  try {
    let params = { leg_id: legId }
    let response = await axios.get(endpoint, { params })
    let data = response.data
    console.log(data)
    let leg = responseToLeg(data)
    return leg
  } catch (e) {
    console.log(e)
    return undefined
  }
}
