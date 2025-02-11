import { parse as parseDuration, Duration } from "tinyduration"

export const getSorter = <T>(
  sortFn: (t1: T, t2: T) => number,
  asc: boolean
) => ({
  sortFn,
  asc,
})

export const sortBy = <T>(
  t1: T,
  t2: T,
  ...params: {
    sortFn: (t1: T, t2: T) => number
    asc: boolean
  }[]
) => {
  for (const { sortFn, asc } of params) {
    let result = sortFn(t1, t2) * (asc ? 1 : -1)
    if (result != 0) {
      return result
    }
  }
  return 0
}

export const durationToHoursAndMinutes = (duration: number) => ({
  hours: Math.floor(duration / 60),
  minutes: duration % 60,
})

const durationToSeconds = (duration: Duration) =>
  (duration.days ?? 0) * 86400 +
  (duration.hours ?? 0) * 3600 +
  (duration.minutes ?? 0) * 60 +
  (duration.seconds ?? 0)

export const getDurationString = (duration: Duration) => {
  let { days, hours, minutes } = duration
  let dayString = days ? `${days}d ` : ""
  return `${dayString}${hours ?? 0}h ${minutes ?? 0}m`
}

export const getMaybeDurationString = (duration: Duration | undefined) =>
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
  duration?: Duration
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
    duration = parseDuration(data.duration)
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

export const getLegOperator = (leg: TrainLeg) => {
  const service = leg.services[0]
  return service.brand ? service.brand.name : service.operator.name
}

export interface LegStat {
  id: number
  boardTime: Date
  boardCrs: string
  boardName: string
  alightTime: Date
  alightCrs: string
  alightName: string
  distance: number
  duration: Duration
  delay: number
  operatorId: number
  operatorCode: string
  operatorName: string
  isBrand: boolean
}

const responseToLegStat = (data: any) => ({
  id: data.leg_id,
  boardTime: new Date(Date.parse(data.board_time)),
  boardCrs: data.board_crs,
  boardName: data.board_name,
  alightTime: new Date(Date.parse(data.alight_time)),
  alightCrs: data.alight_crs,
  alightName: data.alight_name,
  distance: parseFloat(data.distance),
  duration: parseDuration(data.duration),
  delay: data.delay == null ? undefined : data.delay,
  operatorId: data.operator_id,
  operatorCode: data.operator_code,
  operatorName: data.operator_name,
  isBrand: data.is_brand,
})

export namespace LegStatSorter {
  export const byDate = (leg1: LegStat, leg2: LegStat) =>
    leg1.boardTime.getTime() - leg2.boardTime.getTime()
  export const byDistance = (leg1: LegStat, leg2: LegStat) =>
    leg1.distance - leg2.distance
  export const byDuration = (leg1: LegStat, leg2: LegStat) =>
    durationToSeconds(leg1.duration) - durationToSeconds(leg2.duration)
  export const byDelay = (leg1: LegStat, leg2: LegStat) =>
    leg1.delay - leg2.delay
}

export interface StationStat {
  crs: string
  name: string
  operatorName: string
  operatorId: number
  boards: number
  alights: number
  intermediates: number
}

const responseToStationStat = (data: any) => ({
  crs: data.station_crs,
  name: data.station_name,
  operatorName: data.operator_name,
  operatorId: data.operator_id,
  isBrand: data.is_brand,
  boards: data.boards,
  alights: data.alights,
  intermediates: data.intermediates,
})

export const getBoardsPlusAlights = (stn: StationStat) =>
  stn.boards + stn.alights

export namespace StationStatSorter {
  export const byName = (stn1: StationStat, stn2: StationStat) =>
    stn1.name.localeCompare(stn2.name)

  export const byOperator = (stn1: StationStat, stn2: StationStat) =>
    stn1.operatorName.localeCompare(stn2.operatorName)

  export const byBoards = (stn1: StationStat, stn2: StationStat) =>
    stn1.boards - stn2.boards

  export const byAlights = (stn1: StationStat, stn2: StationStat) =>
    stn1.alights - stn2.alights

  export const byBoardsPlusAlights = (stn1: StationStat, stn2: StationStat) =>
    stn1.boards + stn1.alights - (stn2.boards + stn2.alights)

  export const byCalls = (stn1: StationStat, stn2: StationStat) =>
    stn1.intermediates - stn2.intermediates

  export const byTotal = (stn1: StationStat, stn2: StationStat) =>
    stn1.boards + stn1.alights - (stn2.boards + stn2.alights)
}

export interface OperatorStat {
  id: number
  name: string
  isBrand: boolean
  count: number
  distance: number
  duration: Duration
  delay: number
}

const responseToOperatorStat = (data: any) => ({
  id: data.operator_id,
  name: data.operator_name,
  isBrand: data.is_brand,
  count: data.count,
  distance: parseFloat(data.distance),
  duration: parseDuration(data.duration),
  delay: data.delay == null ? undefined : data.delay,
})

export namespace OperatorStatSorter {
  export const byName = (op1: OperatorStat, op2: OperatorStat) =>
    op1.name.localeCompare(op2.name)
  export const byCount = (op1: OperatorStat, op2: OperatorStat) =>
    op1.count - op2.count
  export const byDuration = (op1: OperatorStat, op2: OperatorStat) =>
    durationToSeconds(op1.duration) - durationToSeconds(op2.duration)
  export const byDistance = (op1: OperatorStat, op2: OperatorStat) =>
    op1.distance - op2.distance
  export const byDelay = (op1: OperatorStat, op2: OperatorStat) =>
    op1.delay - op2.delay
}

export interface ClassStat {
  stockClass: number
  count: number
  distance: number
  duration: Duration
}

const responseToClassStat = (data: any) => ({
  stockClass: data.stock_class,
  count: data.count,
  distance: parseFloat(data.distance),
  duration: parseDuration(data.duration),
})

export namespace ClassStatSorter {
  export const byClassNumber = (cls1: ClassStat, cls2: ClassStat) =>
    cls1.stockClass - cls2.stockClass
  export const byCount = (cls1: ClassStat, cls2: ClassStat) =>
    cls1.count - cls2.count
  export const byDistance = (cls1: ClassStat, cls2: ClassStat) =>
    cls1.distance - cls2.distance
  export const byDuration = (cls1: ClassStat, cls2: ClassStat) =>
    durationToSeconds(cls1.duration) - durationToSeconds(cls2.duration)
}

export interface UnitStat {
  stockNumber: number
  count: number
  distance: number
  duration: Duration
}

const responseToUnitStat = (data: any) => ({
  stockNumber: data.stock_number,
  count: data.count,
  distance: parseFloat(data.distance),
  duration: parseDuration(data.duration),
})

export namespace UnitStatSorter {
  export const byUnitNumber = (cls1: UnitStat, cls2: UnitStat) =>
    cls1.stockNumber - cls2.stockNumber
  export const byCount = (cls1: UnitStat, cls2: UnitStat) =>
    cls1.count - cls2.count
  export const byDistance = (cls1: UnitStat, cls2: UnitStat) =>
    cls1.distance - cls2.distance
  export const byDuration = (cls1: UnitStat, cls2: UnitStat) =>
    durationToSeconds(cls1.duration) - durationToSeconds(cls2.duration)
}

export interface Stats {
  journeys: number
  distance: number
  duration: Duration
  delay: number
  legStats: LegStat[]
  stationStats: StationStat[]
  operatorStats: OperatorStat[]
  classStats: ClassStat[]
  unitStats: UnitStat[]
}

export const responseToStats = (data: any) => ({
  journeys: data.journeys,
  distance: data.distance,
  duration: parseDuration(data.duration),
  delay: data.delay,
  legStats: data.leg_stats.map(responseToLegStat),
  stationStats: data.station_stats.map(responseToStationStat),
  operatorStats: !data.operator_stats
    ? []
    : data.operator_stats.map(responseToOperatorStat),
  classStats: !data.class_stats
    ? []
    : data.class_stats.map(responseToClassStat),
  unitStats: !data.unit_stats ? [] : data.unit_stats.map(responseToUnitStat),
})
