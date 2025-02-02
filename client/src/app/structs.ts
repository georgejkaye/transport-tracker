import { parse } from "tinyduration"

export const durationToHoursAndMinutes = (duration: number) => ({
  hours: Math.floor(duration / 60),
  minutes: duration % 60,
})

export const getDurationString = (duration: number) => {
  let { hours, minutes } = durationToHoursAndMinutes(duration)
  return `${hours}h ${minutes}m`
}

export const getMaybeDurationString = (duration: number | undefined) =>
  !duration ? "" : getDurationString(duration)

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

export const dateToLongString = (date: Date) =>
  `${date.toLocaleDateString("en-GB", {
    weekday: "long",
    day: "2-digit",
    month: "long",
    year: "numeric",
  })}`

export const dateToTimeString = (date: Date) =>
  `${date.getHours().toString().padStart(2, "0")}:${date
    .getMinutes()
    .toString()
    .padStart(2, "0")}`

export const maybeDateToTimeString = (date: Date | undefined) =>
  !date ? "" : dateToTimeString(date)

export interface TrainStation {
  crs: string
  name: string
}

export const responseToTrainStation = (data: any) => ({
  crs: data.crs,
  name: data.name,
})

export interface OperatorData {
  id: number
  name: string
  code: string
  fg: string
  bg: string
}

export const responseToOperatorData = (data: any) => ({
  id: data.id,
  name: data.name,
  code: data.code,
  fg: data.fg,
  bg: data.bg,
})

export interface BrandData {
  id: number
  name: string
  code: string
  fg: string
  bg: string
}

export const responseToBrandData = (data: any) => ({
  id: data.id,
  name: data.name,
  code: data.code,
  fg: data.fg,
  bg: data.bg,
})

export interface TrainStationLegData {
  id: number
  platform: string
  origin: TrainStation
  destination: TrainStation
  stopTime: Date
  planArr?: Date
  actArr?: Date
  planDep?: Date
  actDep?: Date
  before?: number
  after?: number
  operator: OperatorData
  brand?: BrandData
}

export const responseToTrainStationLegData = (data: any) => ({
  id: data.id,
  platform: data.platform,
  origin: responseToTrainStation(data.origin),
  destination: responseToTrainStation(data.destination),
  stopTime: responseToDate(data.stop_time),
  planArr: responseToDate(data.plan_arr),
  actArr: responseToDate(data.act_arr),
  planDep: responseToDate(data.plan_dep),
  actDep: responseToDate(data.act_dep),
  before: data.calls_before,
  after: data.calls_after,
  operator: responseToOperatorData(data.operator),
  brand: !data.brand ? undefined : responseToBrandData(data["brand"]),
})

export interface TrainStationData {
  crs: string
  name: string
  operator: OperatorData
  brand?: BrandData
  legs: TrainStationLegData[]
  starts: number
  finishes: number
  intermediates: number
  img?: string
}

export const responseToTrainStationData = (data: any) => ({
  name: data.name,
  crs: data.crs,
  operator: responseToOperatorData(data.operator),
  brand: !data.brand ? undefined : responseToBrandData(data["brand"]),
  legs: data.legs.map(responseToTrainStationLegData),
  starts: data.starts,
  finishes: data.finishes,
  intermediates: data.passes,
  img: !data.img ? undefined : data["img"],
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
  id: data.service_id,
  runDate: data.service_run_date,
  association: responseToAssociationType(data.association),
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
  station: responseToTrainStation(data.station),
  platform: data.platform,
  planArr: responseToDate(data.plan_arr),
  planDep: responseToDate(data.plan_dep),
  actArr: responseToDate(data.act_arr),
  actDep: responseToDate(data.act_dep),
  assocs: !data.assocs ? [] : data.assocs.map(responseToAssociatedTrainService),
  mileage: !data.mileage ? null : parseFloat(data["mileage"]),
})

export interface TrainService {
  id: string
  headcode: string
  runDate: Date
  serviceStart: Date
  origins: TrainStation[]
  destinations: TrainStation[]
  operator: OperatorData
  brand?: BrandData
  power?: string
  calls: TrainCall[]
  assocs: AssociatedTrainService[]
}

export const responseToTrainService = (data: any) => ({
  id: data.service_id,
  headcode: data.headcode,
  runDate: new Date(data.run_date),
  serviceStart: new Date(data.service_start),
  origins: data.origins.map(responseToTrainStation),
  destinations: data.destinations.map(responseToTrainStation),
  operator: responseToOperatorData(data.operator),
  brand: !data.brand.id ? undefined : responseToBrandData(data.brand),
  power: data.power,
  calls: data.calls.map(responseToTrainCall),
  assocs: !data.assocs ? [] : data.assocs.map(responseToAssociatedTrainService),
})

const getServiceEndpointString = (stations: TrainStation[]) => {
  var returnString = ""
  for (let i = 0; i < stations.length; i++) {
    let station = stations[i]
    let stationName = station.name
    if (i == 0) {
      returnString = stationName
    } else if (i == stations.length - 1) {
      returnString = `${returnString} & ${stationName}`
    } else {
      returnString = `${returnString}, ${stationName}`
    }
  }
  return returnString
}

export const getTrainServiceString = (service: TrainService) =>
  `${service.headcode} ${dateToTimeString(
    service.serviceStart
  )} ${getServiceEndpointString(service.origins)} to ${getServiceEndpointString(
    service.destinations
  )}`

export interface TrainStockReport {
  classNo?: number
  subclassNo?: number
  stockNo?: number
  cars?: number
}

export const responseToTrainStockReport = (data: any) => ({
  classNo: data.class_no ? data["class_no"] : undefined,
  subclassNo: data.subclass_no ? data["subclass_no"] : undefined,
  stockNo: data.stock_no ? data["stock_no"] : undefined,
  cars: !data.cars
    ? undefined
    : data.cars["cars"]
    ? data.cars["cars"]
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
  point?: [number, number]
}

export const responseToTrainLegCall = (data: any) => ({
  station: responseToTrainStation(data.station),
  platform: data.platform ? data["platform"] : undefined,
  planArr: responseToDate(data.plan_arr),
  planDep: responseToDate(data.plan_dep),
  actArr: responseToDate(data.act_arr),
  actDep: responseToDate(data.act_dep),
  associatedService: !data.associated_service
    ? undefined
    : responseToAssociatedTrainService(data.associated_service),
  newStock: !data.leg_stock
    ? undefined
    : data.leg_stock.map(responseToTrainStockReport),
  mileage: !data.mileage ? undefined : parseFloat(data["mileage"]),
  point: !data.point
    ? undefined
    : [parseFloat(data.point[0]), parseFloat(data.point[1])],
})

export interface TrainLegSegment {
  start: TrainStation
  end: TrainStation
  mileage?: number
  stocks: TrainStockReport[]
}

export const responseToTrainLegSegment = (data: any) => {
  return {
    start: responseToTrainStation(data.start),
    end: responseToTrainStation(data.end),
    mileage: !data.mileage ? undefined : parseFloat(data["mileage"]),
    stocks: data.stocks.map(responseToTrainStockReport),
  }
}

export interface TrainLeg {
  id: number
  start: Date
  services: TrainService[]
  calls: TrainLegCall[]
  stock: TrainLegSegment[]
  distance?: number
  // duration in minutes
  duration?: number
  geometry?: [number, number][]
}

export const getLegOrigin = (leg: TrainLeg) => leg.calls[0]
export const getLegDestination = (leg: TrainLeg) =>
  leg.calls[leg.calls.length - 1]

const responseToGeometry = (data: [string, string][]): [number, number][] =>
  data.map((point) => [parseFloat(point[0]), parseFloat(point[1])])

export const responseToLeg = (data: any): TrainLeg => {
  let services = []
  for (const id in data.services) {
    let service = data.services[id]
    services.push(responseToTrainService(service))
  }
  var duration
  try {
    let { hours, minutes } = parse(data.duration)
    duration = (hours ? hours * 60 : 0) + (minutes ? minutes : 0)
  } catch {
    duration = undefined
  }
  const geometry = !data.geometry
    ? undefined
    : responseToGeometry(data.geometry)
  return {
    id: data.id,
    start: new Date(data.leg_start),
    services,
    calls: data.calls.map(responseToTrainLegCall),
    stock: data.stocks.map(responseToTrainLegSegment),
    distance: !data.distance ? undefined : parseFloat(data["distance"]),
    duration,
    geometry,
  }
}

export const getLegColour = (leg: TrainLeg) => {
  const service = leg.services[0]
  return service.brand ? service.brand.bg : service.operator.bg
}
