import { parse } from "tinyduration"

export const durationToHoursAndMinutes = (duration: number) => ({
  hours: Math.floor(duration / 60),
  minutes: duration % 60,
})

export const getDurationString = (duration: number) => {
  let { hours, minutes } = durationToHoursAndMinutes(duration)
  return `${hours}h ${minutes}m`
}

export const mileageToMilesAndChains = (miles: number) => ({
  miles: Math.floor(miles),
  chains: (miles * 80) % 80,
})

export const getMilesAndChainsString = (mileage: number) => {
  let { miles, chains } = mileageToMilesAndChains(mileage)
  return `${miles}m ${Math.round(chains)}ch`
}

export const responseToDate = (data: any) =>
  data === null ? undefined : new Date(data)

export const dateToShortString = (date: Date) =>
  `${date.getFullYear()}-${(date.getMonth() + 1)
    .toString()
    .padStart(2, "0")}-${date.getDate().toString().padStart(2, "0")}`

export const dateToTimeString = (date: Date) =>
  `${date.getHours().toString().padStart(2, "0")}:${date
    .getMinutes()
    .toString()
    .padStart(2, "0")}`

export interface TrainStation {
  crs: string
  name: string
}

export const responseToTrainStation = (data: any) => ({
  crs: data["crs"],
  name: data["name"],
})

export const enum AssociationType {
  DIVIDES_TO,
  DIVIDES_FROM,
  JOINS_WITH,
  JOINS_TO,
}

export const responseToAssociationType = (data: any) => {
  if (data === "DIVIDES_TO") {
    return AssociationType.DIVIDES_TO
  } else if (data === "DIVIDES_FROM") {
    return AssociationType.DIVIDES_FROM
  } else if (data === "JOINS_WITH") {
    return AssociationType.JOINS_WITH
  } else if (data === "JOINS_TO") {
    return AssociationType.JOINS_TO
  }
}

export interface AssociatedTrainService {
  id: string
  runDate: Date
  assocation: AssociationType
}

export const responseToAssociatedTrainService = (data: any) => ({
  id: data["service_id"],
  runDate: data["service_run_date"],
  association: responseToAssociationType(data["association"]),
})

export interface TrainCall {
  station: TrainStation
  platform?: string
  planArr?: Date
  planDep?: Date
  actArr?: Date
  actDep?: Date
  assocs: AssociatedTrainService[]
  mileage?: number
}

export const responseToTrainCall = (data: any) => ({
  station: responseToTrainStation(data["station"]),
  platform: data["platform"],
  planArr: responseToDate(data["plan_arr"]),
  planDep: responseToDate(data["plan_dep"]),
  actArr: responseToDate(data["act_arr"]),
  actDep: responseToDate(data["act_dep"]),
  assocs: data.assocs.map(responseToAssociatedTrainService),
  mileage: !data["mileage"] ? null : parseFloat(data["mileage"]),
})

export interface TrainService {
  id: string
  headcode: string
  runDate: Date
  serviceStart: Date
  origins: TrainStation[]
  destinations: TrainStation[]
  operatorId: string
  operatorName: string
  brandId?: string
  brandName?: string
  power?: string
  calls: TrainCall[]
  assocs: AssociatedTrainService[]
}

export const responseToTrainService = (data: any) => ({
  id: data["service_id"],
  headcode: data["headcode"],
  runDate: new Date(data["run_date"]),
  serviceStart: new Date(data["service_start"]),
  origins: data["origins"].map(responseToTrainStation),
  destinations: data["destinations"].map(responseToTrainStation),
  operatorName: data["operator_name"],
  operatorId: data["operator_id"],
  brandId: data["brand_id"],
  brandName: data["brand_name"],
  power: data["power"],
  calls: data["calls"].map(responseToTrainCall),
  assocs: data["assocs"].map(responseToAssociatedTrainService),
})

export interface TrainStockReport {
  classNo?: number
  subclassNo?: number
  stockNo?: number
  cars?: number
}

export const responseToTrainStockReport = (data: any) => ({
  classNo: data["class_no"] ? data["class_no"] : undefined,
  subclassNo: data["subclass_no"] ? data["subclass_no"] : undefined,
  stockNo: data["stock_no"] ? data["stock_no"] : undefined,
  cars: !data["cars"]
    ? undefined
    : data["cars"]["cars"]
    ? data["cars"]["cars"]
    : undefined,
})

export interface TrainLegCall {
  station: TrainStation
  platform?: string
  planArr?: Date
  planDep?: Date
  actArr?: Date
  actDep?: Date
  associatedService?: AssociatedTrainService
  newStock?: TrainStockReport[]
  mileage?: number
}

export const responseToTrainLegCall = (data: any) => ({
  station: responseToTrainStation(data["station"]),
  platform: data["platform"] ? data["platform"] : undefined,
  planArr: responseToDate(data["plan_arr"]),
  planDep: responseToDate(data["plan_dep"]),
  actArr: responseToDate(data["act_arr"]),
  actDep: responseToDate(data["act_dep"]),
  associatedService: !data["associated_service"]
    ? undefined
    : responseToAssociatedTrainService(data["associated_service"]),
  newStock: !data["leg_stock"]
    ? undefined
    : data["leg_stock"].map(responseToTrainStockReport),
  mileage: !data["mileage"] ? undefined : parseFloat(data["mileage"]),
})

export interface TrainLegSegment {
  start: TrainStation
  end: TrainStation
  mileage?: number
  stocks: TrainStockReport[]
}

export const responseToTrainLegSegment = (data: any) => ({
  start: responseToTrainStation(data["start"]),
  end: responseToTrainStation(data["end"]),
  mileage: !data["mileage"] ? undefined : parseFloat(data["mileage"]),
  stocks: data["stocks"].map(responseToTrainStockReport),
})

export interface TrainLeg {
  id: number
  start: Date
  services: Map<string, TrainService>
  calls: TrainLegCall[]
  stock: TrainLegSegment[]
  distance?: number
  // duration in minutes
  duration: number
}

export const getLegOrigin = (leg: TrainLeg) => leg.calls[0]
export const getLegDestination = (leg: TrainLeg) =>
  leg.calls[leg.calls.length - 1]

export const responseToLeg = (data: any) => {
  let services = new Map()
  for (const id in data["services"]) {
    let service = data["services"][id]
    services.set(id, responseToTrainService(service))
  }
  let { hours, minutes } = parse(data["duration"])
  let duration = (hours ? hours * 60 : 0) + (minutes ? minutes : 0)
  return {
    id: data["id"],
    start: new Date(data["leg_start"]),
    services,
    calls: data["calls"].map(responseToTrainLegCall),
    stock: data["stocks"].map(responseToTrainLegSegment),
    distance: !data["distance"] ? undefined : parseFloat(data["distance"]),
    duration,
  }
}
