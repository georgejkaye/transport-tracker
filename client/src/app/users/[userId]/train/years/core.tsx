import {
  LegIconLink,
  EndpointSection,
  TotalStat,
  getDelayStyle,
  getDelay,
  getDelayString,
} from "@/app/leg"
import {
  TrainLeg,
  getMilesAndChainsString,
  getLegOrigin,
  getLegDestination,
  dateToShortString,
  getMaybeDurationString,
  getDurationString,
  StationStat,
  StationStatSorter,
  sortBy,
  getSorter,
  OperatorStat,
  OperatorStatSorter,
  Stats,
  ClassStat,
  ClassStatSorter,
  UnitStat,
  UnitStatSorter,
  LegStat,
  LegStatSorter,
} from "@/app/structs"
import Link from "next/link"
import { useEffect, useState } from "react"
import { FaAngleUp, FaAngleDown } from "react-icons/fa6"

const LegRow = (props: { userId: number; leg: TrainLeg }) => {
  let { leg, userId } = props
  let mileString = !leg.distance ? "" : getMilesAndChainsString(leg.distance)
  let origin = getLegOrigin(leg)
  let destination = getLegDestination(leg)
  return (
    <div className="flex flex-row gap-4 justify-center">
      <div className="flex flex-col lg:flex-row gap-4">
        <div className="flex flex-row gap-2 lg:w-80 items-center">
          <LegIconLink userId={userId} legId={leg.id} />
          <div className="text-xs lg:hidden">•</div>
          <div className="lg:px-2">{dateToShortString(leg.start)}</div>
          <div className="text-xs lg:hidden">•</div>
          <div className="lg:w-28">{getMaybeDurationString(leg.duration)}</div>
          <div className="text-xs lg:hidden">•</div>
          <div className="lg:w-32">{mileString}</div>
        </div>
        <div className="flex flex-col md:flex-row gap-2">
          <div className="flex flex-row gap-2 items-center">
            <div className="text-right w-10 text-xs lg:hidden">from</div>
            <EndpointSection userId={userId} call={origin} origin={true} />
          </div>
          <div className="flex flex-row gap-2 items-center">
            <div className="text-right w-10 text-xs lg:hidden">to</div>
            <EndpointSection
              userId={userId}
              call={destination}
              origin={false}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

export const GeneralStats = (props: { stats: Stats }) => {
  let { stats } = props
  return (
    <div className="flex flex-row flex-wrap gap-4 py-2">
      <TotalStat title="Legs" value={`${stats.legStats.length}`} />
      <TotalStat
        title="Distance"
        value={getMilesAndChainsString(stats.distance)}
      />
      <TotalStat title="Duration" value={getDurationString(stats.duration)} />
    </div>
  )
}

interface TableColumn<T> {
  style: string
  title: string
  getValue: (t: T) => JSX.Element | string | number
  getOrder: (t1: T, t2: T, natural: boolean) => number
  naturalOrderAscending: boolean
  allowSortingBy: boolean
}

const SortableTable = <T,>(props: {
  title: string
  colour: string
  columns: TableColumn<T>[]
  values: T[]
  numberToShow: number
  getKey: (t: T) => string
  rankSort: (t1: T, t2: T, natural: boolean) => number
}) => {
  let { title, colour, columns, values, numberToShow, getKey, rankSort } = props
  let [sortedValues, setSortedValues] = useState(
    values
      .toSorted((t1, t2) => rankSort(t1, t2, true))
      .map((val, i) => ({ originalRank: i, value: val }))
  )
  let [sortingColumn, setSortingColumn] = useState(-1)
  let [sortingNaturalOrder, setSortingNaturalOrder] = useState(true)
  let [extended, setExtended] = useState(false)

  useEffect(() => {
    setSortedValues((values) =>
      values.toSorted((t1, t2) =>
        sortingColumn == -1
          ? (t1.originalRank - t2.originalRank) * (sortingNaturalOrder ? 1 : -1)
          : columns[sortingColumn].getOrder(
              t1.value,
              t2.value,
              sortingNaturalOrder
            )
      )
    )
  }, [sortingColumn, sortingNaturalOrder])

  const onClickToggleExtended = (_e: React.MouseEvent<HTMLDivElement>) =>
    setExtended((prev) => !prev)

  const ColumnHeader = (props: {
    i: number
    title: string
    style: string
    naturalOrderAscending: boolean
    allowSortingBy: boolean
  }) => {
    let { i, title, style, naturalOrderAscending, allowSortingBy } = props
    const onClickHeader = (_e: React.MouseEvent<HTMLDivElement>) => {
      if (allowSortingBy) {
        if (sortingColumn == i) {
          setSortingNaturalOrder((prev) => !prev)
        } else {
          setSortingColumn(i)
          setSortingNaturalOrder(true)
        }
      }
    }
    const SortingArrow = (props: { i: number }) =>
      sortingColumn == props.i &&
      (sortingNaturalOrder === naturalOrderAscending ? (
        <FaAngleUp />
      ) : (
        <FaAngleDown />
      ))
    return (
      <div
        className={`flex flex-row gap-1 items-center font-bold ${style} ${
          allowSortingBy ? "cursor-pointer" : ""
        }`}
        onClick={onClickHeader}
      >
        <div>{title}</div>
        <SortingArrow i={i} />
      </div>
    )
  }

  return (
    <div
      className="flex rounded flex-col border-2 pb-2 flex-1"
      style={{ borderColor: colour }}
    >
      <div
        className="p-2 font-bold text-white"
        style={{ backgroundColor: colour }}
      >
        {title}
      </div>
      <div className="flex flex-row p-2 gap-2 px-4">
        {
          <ColumnHeader
            i={-1}
            title="#"
            style="w-10"
            naturalOrderAscending={true}
            allowSortingBy={true}
          />
        }
        {columns.map((col, i) => (
          <ColumnHeader
            key={col.title}
            i={i}
            title={col.title}
            style={col.style}
            naturalOrderAscending={col.naturalOrderAscending}
            allowSortingBy={col.allowSortingBy}
          />
        ))}
      </div>
      {sortedValues.map(
        (val, i) =>
          (extended || i < numberToShow) && (
            <div
              className={"p-2 flex flex-row gap-2 px-4 border-t-2"}
              key={getKey(val.value)}
            >
              {
                <div className="w-10">
                  <div>{val.originalRank + 1}</div>
                </div>
              }
              {columns.map((col) => (
                <div
                  key={`${getKey(val.value)}-${col.title}`}
                  className={col.style}
                >
                  {col.getValue(val.value)}
                </div>
              ))}
            </div>
          )
      )}
      {values.length > numberToShow && (
        <div
          className="p-2 px-4 cursor-pointer hover:underline border-t-2"
          onClick={onClickToggleExtended}
        >
          {!extended ? "Show more..." : "Show fewer..."}
        </div>
      )}
    </div>
  )
}

export interface SortProperty<T> {
  name: string
  getOrder: (t1: T, t2: T, natural: boolean) => number
  naturalOrderAscending: boolean
}

export const SortableList = <T,>(props: {
  title: string
  colour: string
  values: T[]
  getItem: (t: T, i: number) => JSX.Element
  sortProperties: SortProperty<T>[]
  getKey: (t: T) => string
  rankSort: (t1: T, t2: T, natural: boolean) => number
}) => {
  let { title, colour, values, getItem, sortProperties, rankSort, getKey } =
    props
  let [sortedValues, setSortedValues] = useState(
    values
      .toSorted((t1, t2) => rankSort(t1, t2, true))
      .map((val, i) => ({ originalRank: i, value: val }))
  )
  let [sortingProperty, setSortingProperty] = useState(-1)
  let [sortingNaturalOrder, setSortingNaturalOrder] = useState(true)
  useEffect(() => {
    setSortedValues((values) =>
      values.toSorted((t1, t2) =>
        sortingProperty == -1
          ? (t1.originalRank - t2.originalRank) * (sortingNaturalOrder ? 1 : -1)
          : sortProperties[sortingProperty].getOrder(
              t1.value,
              t2.value,
              sortingNaturalOrder
            )
      )
    )
  }, [sortingProperty, sortingNaturalOrder])
  return (
    <div
      className="flex rounded flex-col border-2 pb-2 flex-1"
      style={{ borderColor: colour }}
    >
      <div
        className="p-2 font-bold text-white"
        style={{ backgroundColor: colour }}
      >
        {title}
      </div>
      <div className="flex flex-col">
        {values.map((value, i) => (
          <div key={getKey(value)} className="p-2 px-4 border-b-2">
            {getItem(value, i)}
          </div>
        ))}
      </div>
    </div>
  )
}

export const StationStats = (props: { stats: StationStat[] }) => {
  let { stats } = props
  let stationColumn: TableColumn<StationStat> = {
    style: "flex-1",
    title: "Station",
    getValue: (stn) => (
      <div className="flex flex-row gap-2">
        <div className="font-bold w-12">{stn.crs}</div>
        <div>{stn.name}</div>
      </div>
    ),
    getOrder: (t1, t2, natural) =>
      sortBy(t1, t2, getSorter(StationStatSorter.byName, natural)),
    naturalOrderAscending: true,
    allowSortingBy: true,
  }
  let operatorColumn: TableColumn<StationStat> = {
    style: "w-72",
    title: "Operator",
    getValue: (stn) => stn.operatorName,
    getOrder: (t1, t2, natural) =>
      sortBy(
        t1,
        t2,
        getSorter(StationStatSorter.byOperator, natural),
        getSorter(StationStatSorter.byBoardsPlusAlights, !natural),
        getSorter(StationStatSorter.byBoards, !natural),
        getSorter(StationStatSorter.byAlights, !natural),
        getSorter(StationStatSorter.byCalls, !natural),
        getSorter(StationStatSorter.byName, natural)
      ),
    naturalOrderAscending: true,
    allowSortingBy: true,
  }
  let boardsColumn: TableColumn<StationStat> = {
    style: "w-14",
    title: "B",
    getValue: (stn) => stn.boards,
    getOrder: (stn1, stn2, natural) =>
      sortBy(
        stn1,
        stn2,
        getSorter(StationStatSorter.byBoards, !natural),
        getSorter(StationStatSorter.byAlights, !natural),
        getSorter(StationStatSorter.byCalls, !natural),
        getSorter(StationStatSorter.byName, true)
      ),
    naturalOrderAscending: false,
    allowSortingBy: true,
  }
  let alightsColumn: TableColumn<StationStat> = {
    style: "w-14",
    title: "A",
    getValue: (stn) => stn.alights,
    getOrder: (stn1, stn2, natural) =>
      sortBy(
        stn1,
        stn2,
        getSorter(StationStatSorter.byAlights, !natural),
        getSorter(StationStatSorter.byBoards, !natural),
        getSorter(StationStatSorter.byCalls, !natural),
        getSorter(StationStatSorter.byName, true)
      ),
    naturalOrderAscending: false,
    allowSortingBy: true,
  }
  let boardsPlusAlightsColumn: TableColumn<StationStat> = {
    style: "w-14",
    title: "B+A",
    getValue: (stn) => stn.boards + stn.alights,
    getOrder: (stn1, stn2, natural) =>
      sortBy(
        stn1,
        stn2,
        getSorter(StationStatSorter.byBoardsPlusAlights, !natural),
        getSorter(StationStatSorter.byBoards, !natural),
        getSorter(StationStatSorter.byAlights, !natural),
        getSorter(StationStatSorter.byCalls, !natural),
        getSorter(StationStatSorter.byName, true)
      ),
    naturalOrderAscending: false,
    allowSortingBy: true,
  }
  let callsColumn: TableColumn<StationStat> = {
    style: "w-14",
    title: "C",
    getValue: (stn) => stn.intermediates,
    getOrder: (stn1, stn2, natural) =>
      sortBy(
        stn1,
        stn2,
        getSorter(StationStatSorter.byCalls, !natural),
        getSorter(StationStatSorter.byBoards, !natural),
        getSorter(StationStatSorter.byAlights, !natural),
        getSorter(StationStatSorter.byName, true)
      ),
    naturalOrderAscending: false,
    allowSortingBy: true,
  }
  let totalColumn: TableColumn<StationStat> = {
    style: "w-14",
    title: "T",
    getValue: (stn) => stn.boards + stn.alights + stn.intermediates,
    getOrder: (stn1, stn2, natural) =>
      sortBy(
        stn1,
        stn2,
        getSorter(StationStatSorter.byTotal, !natural),
        getSorter(StationStatSorter.byBoards, !natural),
        getSorter(StationStatSorter.byAlights, !natural),
        getSorter(StationStatSorter.byCalls, !natural),
        getSorter(StationStatSorter.byName, true)
      ),
    naturalOrderAscending: false,
    allowSortingBy: true,
  }
  let columns = [
    stationColumn,
    operatorColumn,
    boardsColumn,
    alightsColumn,
    boardsPlusAlightsColumn,
    callsColumn,
    totalColumn,
  ]
  const getStationItem = (station: StationStat, i: number) => (
    <div className="flex flex-col gap-2">
      <div className="flex flex-row gap-2 flex-wrap">
        <div className="w-10">{i}</div>
        <div className="w-12">
          <b>{station.crs}</b>
        </div>
        <div className="flex-1">{station.name}</div>
        <div className="w-72">{station.operatorName}</div>
      </div>
      <div className="flex flex-row gap-4">
        <div>{station.boards} B</div>
        <div>{station.alights} A</div>
        <div>{station.boards + station.alights} B+A</div>
        <div>{station.intermediates} C</div>
        <div>{station.boards + station.alights + station.intermediates} T</div>
      </div>
    </div>
  )
  const stationRankSort = (
    stn1: StationStat,
    stn2: StationStat,
    natural: boolean
  ) =>
    sortBy(
      stn1,
      stn2,
      getSorter(StationStatSorter.byBoardsPlusAlights, !natural),
      getSorter(StationStatSorter.byBoards, !natural),
      getSorter(StationStatSorter.byAlights, !natural),
      getSorter(StationStatSorter.byCalls, !natural),
      getSorter(StationStatSorter.byName, true)
    )

  return (
    <div>
      <div className="lg:hidden">
        <SortableList
          title="Stations"
          colour="#db2700"
          values={stats}
          getItem={getStationItem}
          sortProperties={[]}
          getKey={(stn) => stn.crs}
          rankSort={stationRankSort}
        />
      </div>
      <div className="hidden lg:flex">
        <SortableTable
          title="Stations"
          colour="#db2700"
          columns={columns}
          values={stats}
          numberToShow={10}
          getKey={(stn) => stn.crs}
          rankSort={stationRankSort}
        />
      </div>
    </div>
  )
}

export const OperatorStats = (props: { stats: OperatorStat[] }) => {
  let { stats } = props
  let operatorColumn: TableColumn<OperatorStat> = {
    style: "w-96 flex-1",
    title: "Operator",
    getValue: (op) => op.name,
    getOrder: (t1, t2, natural) =>
      sortBy(t1, t2, getSorter(OperatorStatSorter.byName, natural)),
    naturalOrderAscending: true,
    allowSortingBy: true,
  }
  let countColumn: TableColumn<OperatorStat> = {
    style: "w-14",
    title: "Legs",
    getValue: (op) => op.count,
    getOrder: (op1, op2, natural) =>
      sortBy(
        op1,
        op2,
        getSorter(OperatorStatSorter.byCount, !natural),
        getSorter(OperatorStatSorter.byName, true)
      ),
    naturalOrderAscending: false,
    allowSortingBy: true,
  }
  let distanceColumn: TableColumn<OperatorStat> = {
    style: "w-32",
    title: "Distance",
    getValue: (op) => getMilesAndChainsString(op.distance),
    getOrder: (op1, op2, natural) =>
      sortBy(
        op1,
        op2,
        getSorter(OperatorStatSorter.byDistance, !natural),
        getSorter(OperatorStatSorter.byName, true)
      ),
    naturalOrderAscending: false,
    allowSortingBy: true,
  }
  let durationColumn: TableColumn<OperatorStat> = {
    style: "w-24",
    title: "Duration",
    getValue: (op) => getDurationString(op.duration),
    getOrder: (op1, op2, natural) =>
      sortBy(
        op1,
        op2,
        getSorter(OperatorStatSorter.byDuration, !natural),
        getSorter(OperatorStatSorter.byName, true)
      ),
    naturalOrderAscending: false,
    allowSortingBy: true,
  }
  let delayColumn: TableColumn<OperatorStat> = {
    style: "w-20",
    title: "Delay",
    getValue: (op) => (
      <div style={{ color: getDelayStyle(op.delay) }}>
        {getDelayString(op.delay)}
      </div>
    ),
    getOrder: (op1, op2, natural) =>
      sortBy(
        op1,
        op2,
        getSorter(OperatorStatSorter.byDelay, !natural),
        getSorter(OperatorStatSorter.byDuration, natural),
        getSorter(OperatorStatSorter.byName, true)
      ),
    naturalOrderAscending: false,
    allowSortingBy: true,
  }
  let columns = [
    operatorColumn,
    countColumn,
    distanceColumn,
    durationColumn,
    delayColumn,
  ]
  return (
    <SortableTable
      title="Operators"
      colour="#0623af"
      columns={columns}
      values={stats}
      numberToShow={10}
      getKey={(op) => `${op.id}-${op.isBrand ? "B" : "O"}`}
      rankSort={(op1, op2, natural) =>
        sortBy(
          op1,
          op2,
          getSorter(OperatorStatSorter.byCount, !natural),
          getSorter(OperatorStatSorter.byDuration, !natural),
          getSorter(OperatorStatSorter.byDistance, !natural)
        )
      }
    />
  )
}

export const ClassStats = (props: { stats: ClassStat[] }) => {
  let { stats } = props
  let classColumn: TableColumn<ClassStat> = {
    style: "flex-1",
    title: "Class",
    getValue: (cls) => `Class ${cls.stockClass}`,
    getOrder: (t1, t2, natural) =>
      sortBy(t1, t2, getSorter(ClassStatSorter.byClassNumber, natural)),
    naturalOrderAscending: true,
    allowSortingBy: true,
  }
  let countColumn: TableColumn<ClassStat> = {
    style: "w-14",
    title: "Legs",
    getValue: (cls) => cls.count,
    getOrder: (cls1, cls2, natural) =>
      sortBy(
        cls1,
        cls2,
        getSorter(ClassStatSorter.byCount, !natural),
        getSorter(ClassStatSorter.byClassNumber, true)
      ),
    naturalOrderAscending: false,
    allowSortingBy: true,
  }
  let distanceColumn: TableColumn<ClassStat> = {
    style: "w-32",
    title: "Distance",
    getValue: (op) => getMilesAndChainsString(op.distance),
    getOrder: (cls1, cls2, natural) =>
      sortBy(
        cls1,
        cls2,
        getSorter(ClassStatSorter.byDistance, !natural),
        getSorter(ClassStatSorter.byClassNumber, true)
      ),
    naturalOrderAscending: false,
    allowSortingBy: true,
  }
  let durationColumn: TableColumn<ClassStat> = {
    style: "w-24",
    title: "Duration",
    getValue: (cls) => getDurationString(cls.duration),
    getOrder: (cls1, cls2, natural) =>
      sortBy(
        cls1,
        cls2,
        getSorter(ClassStatSorter.byDuration, !natural),
        getSorter(ClassStatSorter.byClassNumber, true)
      ),
    naturalOrderAscending: false,
    allowSortingBy: true,
  }
  let columns = [classColumn, countColumn, distanceColumn, durationColumn]
  return (
    <SortableTable
      title="Classes"
      colour="#008f3e"
      columns={columns}
      values={stats}
      numberToShow={10}
      getKey={(cls) => cls.stockClass.toString()}
      rankSort={(cls1, cls2, natural) =>
        sortBy(
          cls1,
          cls2,
          getSorter(ClassStatSorter.byCount, !natural),
          getSorter(ClassStatSorter.byDuration, !natural),
          getSorter(ClassStatSorter.byDistance, !natural)
        )
      }
    />
  )
}

export const UnitStats = (props: { stats: UnitStat[] }) => {
  let { stats } = props
  let classColumn: TableColumn<UnitStat> = {
    style: "flex-1",
    title: "Unit no",
    getValue: (unit) => unit.stockNumber,
    getOrder: (t1, t2, natural) =>
      sortBy(t1, t2, getSorter(UnitStatSorter.byUnitNumber, natural)),
    naturalOrderAscending: true,
    allowSortingBy: true,
  }
  let countColumn: TableColumn<UnitStat> = {
    style: "w-14",
    title: "Legs",
    getValue: (unit) => unit.count,
    getOrder: (unit1, unit2, natural) =>
      sortBy(
        unit1,
        unit2,
        getSorter(UnitStatSorter.byCount, !natural),
        getSorter(UnitStatSorter.byDistance, !natural),
        getSorter(UnitStatSorter.byDuration, !natural),
        getSorter(UnitStatSorter.byUnitNumber, true)
      ),
    naturalOrderAscending: false,
    allowSortingBy: true,
  }
  let distanceColumn: TableColumn<UnitStat> = {
    style: "w-32",
    title: "Distance",
    getValue: (op) => getMilesAndChainsString(op.distance),
    getOrder: (cls1, cls2, natural) =>
      sortBy(
        cls1,
        cls2,
        getSorter(UnitStatSorter.byDistance, !natural),
        getSorter(UnitStatSorter.byUnitNumber, true)
      ),
    naturalOrderAscending: false,
    allowSortingBy: true,
  }
  let durationColumn: TableColumn<UnitStat> = {
    style: "w-24",
    title: "Duration",
    getValue: (cls) => getDurationString(cls.duration),
    getOrder: (cls1, cls2, natural) =>
      sortBy(
        cls1,
        cls2,
        getSorter(UnitStatSorter.byDuration, !natural),
        getSorter(UnitStatSorter.byUnitNumber, true)
      ),
    naturalOrderAscending: false,
    allowSortingBy: true,
  }
  let columns = [classColumn, countColumn, distanceColumn, durationColumn]
  return (
    <SortableTable
      title="Units"
      colour="#6200a1"
      columns={columns}
      values={stats}
      numberToShow={10}
      getKey={(unit) => unit.stockNumber.toString()}
      rankSort={(unit1, unit2, natural) =>
        sortBy(
          unit1,
          unit2,
          getSorter(UnitStatSorter.byCount, !natural),
          getSorter(UnitStatSorter.byDuration, !natural),
          getSorter(UnitStatSorter.byDistance, !natural)
        )
      }
    />
  )
}

export const LegStats = (props: { stats: LegStat[] }) => {
  let { stats } = props
  let dateColumn: TableColumn<LegStat> = {
    style: "w-28",
    title: "Date",
    getValue: (leg) => dateToShortString(leg.boardTime),
    getOrder: (t1, t2, natural) =>
      sortBy(t1, t2, getSorter(LegStatSorter.byDate, natural)),
    naturalOrderAscending: true,
    allowSortingBy: true,
  }
  let descriptionColumn: TableColumn<LegStat> = {
    style: "flex-1",
    title: "Leg",
    getValue: (leg) => (
      <Link href={`/users/${leg.user}/train/legs/${leg.id}`}>
        <div>
          <b>{leg.boardName}</b> to <b>{leg.alightName}</b>
        </div>
      </Link>
    ),
    getOrder: (t1, t2, natural) =>
      sortBy(t1, t2, getSorter(LegStatSorter.byDate, natural)),
    naturalOrderAscending: true,
    allowSortingBy: false,
  }
  let operatorColumn: TableColumn<LegStat> = {
    style: "w-10",
    title: "",
    getValue: (leg) => leg.operatorCode,
    getOrder: (t1, t2, natural) =>
      sortBy(t1, t2, getSorter(LegStatSorter.byDate, true)),
    naturalOrderAscending: true,
    allowSortingBy: false,
  }
  let distanceColumn: TableColumn<LegStat> = {
    style: "w-28",
    title: "Distance",
    getValue: (leg) => getMilesAndChainsString(leg.distance),
    getOrder: (t1, t2, natural) =>
      sortBy(
        t1,
        t2,
        getSorter(LegStatSorter.byDistance, !natural),
        getSorter(LegStatSorter.byDate, true)
      ),
    naturalOrderAscending: false,
    allowSortingBy: true,
  }
  let durationColumn: TableColumn<LegStat> = {
    style: "w-28",
    title: "Duration",
    getValue: (leg) => getDurationString(leg.duration),
    getOrder: (t1, t2, natural) =>
      sortBy(
        t1,
        t2,
        getSorter(LegStatSorter.byDuration, !natural),
        getSorter(LegStatSorter.byDate, true)
      ),
    naturalOrderAscending: false,
    allowSortingBy: true,
  }
  let delayColumn: TableColumn<LegStat> = {
    style: "w-16",
    title: "Delay",
    getValue: (leg) => (
      <div style={{ color: getDelayStyle(leg.delay) }}>
        {getDelayString(leg.delay)}
      </div>
    ),
    getOrder: (t1, t2, natural) =>
      sortBy(
        t1,
        t2,
        getSorter(LegStatSorter.byDelay, !natural),
        getSorter(LegStatSorter.byDate, true)
      ),
    naturalOrderAscending: false,
    allowSortingBy: true,
  }
  let columns = [
    dateColumn,
    descriptionColumn,
    operatorColumn,
    distanceColumn,
    durationColumn,
    delayColumn,
  ]
  return (
    <SortableTable
      title="Legs"
      colour="#008eb5"
      columns={columns}
      values={stats}
      numberToShow={10}
      getKey={(leg) => leg.id.toString()}
      rankSort={(leg1, leg2, natural) =>
        sortBy(leg1, leg2, getSorter(LegStatSorter.byDate, natural))
      }
    />
  )
}

export const LegList = (props: { userId: number; legs: TrainLeg[] }) =>
  props.legs.map((leg, i) => (
    <div className="flex flex-col gap-2" key={i}>
      <hr className="h-px border-0 bg-gray-600" />
      <LegRow key={leg.id} userId={props.userId} leg={leg} />
    </div>
  ))
