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
