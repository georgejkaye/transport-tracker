"use client"

import { FormEvent, useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import client from "@/app/api/client"
import type { components } from "@/app/api/api"

type ServiceGraphNode = components["schemas"]["ServiceGraphNodeData"]
type ServiceGraphEdge = components["schemas"]["ServiceGraphEdgeData"]
type ServiceGraphData = components["schemas"]["ServiceGraphData"]

interface GraphPosition {
  x: number
  y: number
}

interface GraphLayout {
  positions: Map<string, GraphPosition>
  width: number
  height: number
}

const graphNodeWidth = 184
const graphNodeHeight = 96
const graphNodeRowSpacing = 136
const graphColumnSpacing = 260

const getServiceGraphErrorMessage = (error: unknown) => {
  if (typeof error !== "object" || error === null || !("detail" in error)) {
    return "Could not load service graph."
  }
  if (typeof error.detail === "string") return error.detail
  if (Array.isArray(error.detail)) {
    const messages = error.detail.flatMap((item) =>
      typeof item === "object" &&
        item !== null &&
        "msg" in item &&
        typeof item.msg === "string"
        ? [item.msg]
        : [],
    )
    if (messages.length) return messages.join("; ")
  }
  return "Could not load service graph."
}

const getNodePortOffset = (index: number, count: number) =>
  count === 1
    ? 16
    : -2 + (index / (count - 1)) * (graphNodeHeight - 64)

const getGraphLayout = (tree: ServiceGraphData): GraphLayout => {
  const adjacency = new Map<string, { nodeId: string; step: number }[]>()
  const serviceCountsByNode = new Map<string, Map<string, number>>()
  const incomingEdgesByNode = new Map<string, ServiceGraphEdge[]>()
  const outgoingEdgesByNode = new Map<string, ServiceGraphEdge[]>()
  const services = new Set<string>()
  const serviceTimes = new Map<string, number>()
  for (const node of tree.nodes) {
    adjacency.set(node.id, [])
    serviceCountsByNode.set(node.id, new Map())
    incomingEdgesByNode.set(node.id, [])
    outgoingEdgesByNode.set(node.id, [])
  }
  for (const edge of tree.edges) {
    adjacency.get(edge.source)?.push({ nodeId: edge.target, step: 1 })
    adjacency.get(edge.target)?.push({ nodeId: edge.source, step: -1 })
    outgoingEdgesByNode.get(edge.source)?.push(edge)
    incomingEdgesByNode.get(edge.target)?.push(edge)
    services.add(edge.service)
    const edgeTime = [
      edge.act_arr ?? edge.plan_arr,
      edge.act_dep ?? edge.plan_dep,
    ]
      .filter((time): time is string => time !== null)
      .map((time) => Date.parse(time))
      .filter(Number.isFinite)
    if (edgeTime.length) {
      serviceTimes.set(
        edge.service,
        Math.min(serviceTimes.get(edge.service) ?? Infinity, ...edgeTime),
      )
    }
    for (const nodeId of [edge.source, edge.target]) {
      const serviceCounts = serviceCountsByNode.get(nodeId)
      if (serviceCounts) {
        serviceCounts.set(
          edge.service,
          (serviceCounts.get(edge.service) ?? 0) + 1,
        )
      }
    }
  }

  const rootId = adjacency.has(tree.root) ? tree.root : tree.nodes[0]?.id
  if (!rootId) {
    return { positions: new Map(), width: 0, height: 0 }
  }

  const orderedServices = [...services].sort(
    (serviceA, serviceB) =>
      (serviceTimes.get(serviceA) ?? Infinity) -
      (serviceTimes.get(serviceB) ?? Infinity) ||
      serviceA.localeCompare(serviceB),
  )
  const rootService = outgoingEdgesByNode.get(rootId)?.[0]?.service
  const hasJunction = tree.nodes.some(
    (node) =>
      new Set(
        (incomingEdgesByNode.get(node.id) ?? []).map((edge) => edge.service),
      ).size > 1 ||
      new Set(
        (outgoingEdgesByNode.get(node.id) ?? []).map((edge) => edge.service),
      ).size > 1,
  )
  const laneServices = [...orderedServices]
  if (hasJunction && rootService) {
    laneServices.splice(laneServices.indexOf(rootService), 1)
    laneServices.splice(Math.floor(laneServices.length / 2), 0, rootService)
  }
  const rootLaneOffset = hasJunction && laneServices.length === 2 ? 1 : 0
  const serviceRows = new Map<string, number>(
    laneServices.map(
      (service, index): [string, number] => [service, index + rootLaneOffset],
    ),
  )

  const ranks = new Map<string, number>([[rootId, 0]])
  const queue = [rootId]
  while (queue.length) {
    const nodeId = queue.shift()
    if (!nodeId) continue
    const rank = ranks.get(nodeId)
    if (rank === undefined) continue
    for (const neighbor of adjacency.get(nodeId) ?? []) {
      if (ranks.has(neighbor.nodeId)) continue
      ranks.set(neighbor.nodeId, rank + neighbor.step)
      queue.push(neighbor.nodeId)
    }
  }

  let nextRank = Math.max(...ranks.values()) + 1
  for (const node of tree.nodes) {
    if (!ranks.has(node.id)) {
      ranks.set(node.id, nextRank)
      nextRank += 1
    }
  }

  const minRank = Math.min(...ranks.values())
  const positions = new Map<string, GraphPosition>()
  const serviceRowsAtNode = new Map<string, Map<string, number>>()
  for (const node of [...tree.nodes].sort(
    (left, right) => (ranks.get(left.id) ?? 0) - (ranks.get(right.id) ?? 0),
  )) {
    const serviceCounts =
      serviceCountsByNode.get(node.id) ?? new Map<string, number>()
    const service = [...serviceCounts]
      .sort(
        ([serviceA, countA], [serviceB, countB]) =>
          countB - countA ||
          (serviceRows.get(serviceA) ?? 0) -
          (serviceRows.get(serviceB) ?? 0),
      )[0]?.[0] ?? node.services[0]
    const incomingEdges = incomingEdgesByNode.get(node.id) ?? []
    const incomingRows = incomingEdges.map(
      (edge) =>
        serviceRowsAtNode.get(node.id)?.get(edge.service) ??
        serviceRows.get(edge.service) ??
        0,
    )
    const outgoingEdges = outgoingEdgesByNode.get(node.id) ?? []
    const outgoingRows = outgoingEdges.map(
      (edge) =>
        serviceRowsAtNode.get(node.id)?.get(edge.service) ??
        serviceRows.get(edge.service) ??
        0,
    )
    const junctionRows = [
      ...(new Set(incomingEdges.map((edge) => edge.service)).size > 1
        ? incomingRows
        : []),
      ...(new Set(outgoingEdges.map((edge) => edge.service)).size > 1
        ? outgoingRows
        : []),
    ]
    const isJoin = new Set(incomingEdges.map((edge) => edge.service)).size > 1
    const row =
      junctionRows.length > 0
        ? (Math.min(...junctionRows) + Math.max(...junctionRows)) /
        2
        : service
          ? (serviceRowsAtNode.get(node.id)?.get(service) ??
            serviceRows.get(service) ??
            0)
          : 0
    positions.set(node.id, {
      x:
        120 +
        ((ranks.get(node.id) ?? 0) - minRank) * graphColumnSpacing,
      y: graphNodeHeight / 2 + 20 + row * graphNodeRowSpacing,
    })
    for (const edge of outgoingEdgesByNode.get(node.id) ?? []) {
      const targetRows =
        serviceRowsAtNode.get(edge.target) ?? new Map<string, number>()
      targetRows.set(
        edge.service,
        isJoin
          ? row
          : (serviceRowsAtNode.get(node.id)?.get(edge.service) ??
            serviceRows.get(edge.service) ??
            row),
      )
      serviceRowsAtNode.set(edge.target, targetRows)
    }
  }

  const verticalPadding = graphNodeHeight / 2 + 20
  const maxRank = Math.max(...ranks.values())
  const maxServiceRow = Math.max(0, ...serviceRows.values())
  return {
    positions,
    width: 240 + (maxRank - minRank) * graphColumnSpacing,
    height: Math.max(
      verticalPadding * 2,
      verticalPadding * 2 + maxServiceRow * graphNodeRowSpacing,
    ),
  }
}

const formatTime = (time: string | null) =>
  time
    ? new Date(time).toLocaleTimeString("en-GB", {
      hour: "2-digit",
      minute: "2-digit",
    })
    : "—"

const getCallTime = (nodeId: string, edges: ServiceGraphEdge[]) => {
  const times = edges
    .filter((edge) => edge.source === nodeId || edge.target === nodeId)
    .flatMap((edge) => [
      edge.plan_arr,
      edge.act_arr,
      edge.plan_dep,
      edge.act_dep,
    ])
    .filter((time): time is string => time !== null)
    .map((time) => Date.parse(time))
    .filter(Number.isFinite)
  return times.length ? Math.min(...times) : Number.POSITIVE_INFINITY
}

const getRelationTime = (
  edge: ServiceGraphEdge,
  direction: "arrival" | "departure",
) => {
  const plan = direction === "arrival" ? edge.plan_arr : edge.plan_dep
  const actual = direction === "arrival" ? edge.act_arr : edge.act_dep
  const time = actual ?? plan
  return time ? Date.parse(time) : Number.POSITIVE_INFINITY
}

const sortRelationsByTime = (
  edges: ServiceGraphEdge[],
  direction: "arrival" | "departure",
) =>
  [...edges].sort(
    (left, right) =>
      getRelationTime(left, direction) - getRelationTime(right, direction) ||
      left.service.localeCompare(right.service),
  )

const sortCallsByTime = (nodes: ServiceGraphNode[], edges: ServiceGraphEdge[]) =>
  [...nodes].sort(
    (left, right) =>
      getCallTime(left.id, edges) - getCallTime(right.id, edges) ||
      left.id.localeCompare(right.id),
  )

const nodeName = (node: ServiceGraphNode | undefined) =>
  node?.location ?? "Unknown location"

const RelationCard = ({
  edge,
  neighbor,
  direction,
  onSelect,
}: {
  edge: ServiceGraphEdge
  neighbor: ServiceGraphNode | undefined
  direction: "arrival" | "departure"
  onSelect: () => void
}) => {
  const plan = direction === "arrival" ? edge.plan_arr : edge.plan_dep
  const actual = direction === "arrival" ? edge.act_arr : edge.act_dep
  return (
    <button
      type="button"
      onClick={onSelect}
      className="w-full rounded-xl border border-slate-200 bg-white p-4 text-left transition hover:border-blue-300 hover:bg-blue-50"
    >
      <div className="flex items-center justify-between gap-3">
        <span className="font-semibold text-slate-900">
          {nodeName(neighbor)}
        </span>
        <span className="text-xs font-medium uppercase tracking-wide text-slate-500">
          {direction === "arrival" ? "arrives" : "departs"}
        </span>
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-slate-600">
        <span>
          Plan <b className="text-slate-800">{formatTime(plan)}</b>
        </span>
        <span>
          Actual <b className="text-slate-800">{formatTime(actual)}</b>
        </span>
      </div>
      <div className="mt-2">
        <span className="rounded-full bg-slate-100 px-2 py-0.5 font-mono text-xs text-slate-700">
          {edge.service}
        </span>
      </div>
    </button>
  )
}

export default function TrainServiceGraphPage({
  initialIdentity = "",
  initialDepartureDate = "",
}: {
  initialIdentity?: string
  initialDepartureDate?: string
}) {
  const router = useRouter()
  const [identity, setIdentity] = useState(initialIdentity)
  const [departureDate, setDepartureDate] = useState(initialDepartureDate)
  const [search, setSearch] = useState("")
  const {
    data: tree,
    error,
    isLoading: loading,
  } = client.useQuery(
    "get",
    "/train/service/graph/{identity}/{departure_date}",
    {
      params: {
        path: {
          identity: initialIdentity,
          departure_date: initialDepartureDate,
        },
      },
    },
    { enabled: Boolean(initialIdentity && initialDepartureDate) },
  )
  const getInitialSelectedNodes = () => {
    if (!tree) {
      return []
    }
    const rootNode = tree.nodes.find((node) => node.id === tree.root)
    const rootStation = rootNode
      ? nodeName(rootNode).trim().toLocaleLowerCase()
      : undefined
    return rootStation
      ? tree.nodes
        .filter(
          (node) =>
            nodeName(node).trim().toLocaleLowerCase() === rootStation,
        )
        .map((node) => node.id)
      : [tree.root]
  }
  const [selectedNodeIds, setSelectedNodeIds] = useState<string[]>(getInitialSelectedNodes())

  const nodesById = useMemo(
    () =>
      new Map(
        tree?.nodes.map(
          (node): [string, ServiceGraphNode] => [node.id, node],
        ) ?? [],
      ),
    [tree],
  )
  const selectedNodes = selectedNodeIds
    .map((nodeId) => nodesById.get(nodeId))
    .filter((node): node is ServiceGraphNode => node !== undefined)
  const selectedNode = selectedNodes[0]
  const graphLayout = useMemo(
    () => (tree ? getGraphLayout(tree) : undefined),
    [tree],
  )
  const edgePortOffsets = useMemo(() => {
    const offsets = new Map<
      ServiceGraphEdge,
      { source: number; target: number }
    >()
    if (!tree || !graphLayout) return offsets

    for (const node of tree.nodes) {
      const position = graphLayout.positions.get(node.id)
      if (!position) continue
      const outgoing = tree.edges
        .filter((edge) => edge.source === node.id)
        .sort((left, right) => {
          const leftTarget = graphLayout.positions.get(left.target)?.y ?? 0
          const rightTarget = graphLayout.positions.get(right.target)?.y ?? 0
          return (
            leftTarget - rightTarget ||
            left.service.localeCompare(right.service) ||
            left.target.localeCompare(right.target)
          )
        })
      outgoing.forEach((edge, index) => {
        const edgeOffsets = offsets.get(edge) ?? { source: 0, target: 0 }
        edgeOffsets.source = getNodePortOffset(index, outgoing.length)
        offsets.set(edge, edgeOffsets)
      })

      const incoming = tree.edges
        .filter((edge) => edge.target === node.id)
        .sort((left, right) => {
          const leftSource = graphLayout.positions.get(left.source)?.y ?? 0
          const rightSource = graphLayout.positions.get(right.source)?.y ?? 0
          return (
            leftSource - rightSource ||
            left.service.localeCompare(right.service) ||
            left.source.localeCompare(right.source)
          )
        })
      incoming.forEach((edge, index) => {
        const edgeOffsets = offsets.get(edge) ?? { source: 0, target: 0 }
        edgeOffsets.target = getNodePortOffset(index, incoming.length)
        offsets.set(edge, edgeOffsets)
      })
    }

    return offsets
  }, [graphLayout, tree])
  const visibleStationGroups = useMemo(() => {
    const query = search.trim().toLocaleLowerCase()
    const groups = new Map<
      string,
      { location: string; shortCodes: Set<string>; nodes: ServiceGraphNode[] }
    >()
    for (const node of tree?.nodes ?? []) {
      const location = nodeName(node)
      const key = location.trim().toLocaleLowerCase()
      const group = groups.get(key) ?? {
        location,
        shortCodes: new Set<string>(),
        nodes: [],
      }
      node.short_codes?.forEach((code) => group.shortCodes.add(code))
      group.nodes.push(node)
      groups.set(key, group)
    }
    for (const group of groups.values()) {
      group.nodes = sortCallsByTime(group.nodes, tree?.edges ?? [])
    }
    return [...groups.entries()]
      .map(([key, group]) => ({ key, ...group }))
      .filter(
        (group) =>
          !query ||
          [
            group.location,
            ...group.shortCodes,
            ...group.nodes.flatMap((node) => node.services),
          ].some((value) => value.toLocaleLowerCase().includes(query)),
      )
  }, [search, tree])
  const selectedCallGroups = sortCallsByTime(
    selectedNodes,
    tree?.edges ?? [],
  ).map((node) => {
    const arrivals = sortRelationsByTime(
      (tree?.edges ?? []).filter((edge) => edge.target === node.id),
      "arrival",
    )
    const departures = sortRelationsByTime(
      (tree?.edges ?? []).filter((edge) => edge.source === node.id),
      "departure",
    )
    return {
      node,
      arrivals,
      departures,
    }
  })

  const loadTree = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const serviceIdentity = identity.trim()
    router.push(
      `/tree/${encodeURIComponent(serviceIdentity)}/${departureDate}`,
    )
  }

  const selectStationCalls = (node: ServiceGraphNode) => {
    const station = nodeName(node).trim().toLocaleLowerCase()
    setSelectedNodeIds(
      (tree?.nodes ?? [])
        .filter(
          (candidate) =>
            nodeName(candidate).trim().toLocaleLowerCase() === station,
        )
        .map((candidate) => candidate.id),
    )
  }
  const selectRoot = () => {
    const rootNode = nodesById.get(tree?.root ?? "")
    if (rootNode) selectStationCalls(rootNode)
  }

  return (
    <div className="space-y-6 py-4">
      <header>
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-blue-800">
          Train services
        </p>
        <h2 className="mt-1 text-3xl font-bold text-slate-950">
          Service graph explorer
        </h2>
        <p className="mt-2 max-w-3xl text-slate-600">
          Explore how a service joins, divides, and continues through its
          station calls. Select any station to follow the connected services.
        </p>
      </header>

      <form
        onSubmit={loadTree}
        className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:grid-cols-[1fr_12rem_auto] sm:items-end"
      >
        <label className="block text-sm font-medium text-slate-700">
          Service identity
          <input
            required
            value={identity}
            onChange={(event) => setIdentity(event.target.value)}
            placeholder="e.g. C82490"
            className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-base text-slate-900 outline-none focus:border-blue-700 focus:ring-2 focus:ring-blue-100"
          />
        </label>
        <label className="block text-sm font-medium text-slate-700">
          Departure date
          <input
            required
            type="date"
            value={departureDate}
            onChange={(event) => setDepartureDate(event.target.value)}
            className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-base text-slate-900 outline-none focus:border-blue-700 focus:ring-2 focus:ring-blue-100"
          />
        </label>
        <button
          type="submit"
          disabled={loading || !identity.trim() || !departureDate}
          className="rounded-lg bg-blue-900 px-5 py-2.5 font-semibold text-white transition hover:bg-blue-800 disabled:cursor-wait disabled:opacity-60"
        >
          {loading ? "Loading…" : "Explore tree"}
        </button>
      </form>

      {error && (
        <div
          role="alert"
          className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-red-800"
        >
          {getServiceGraphErrorMessage(error)}
        </div>
      )}

      {tree && (
        <>
          <div className="grid gap-3 sm:grid-cols-3">
            {[
              ["Stations", tree.nodes.length],
              ["Service links", tree.edges.length],
              [
                "Services",
                new Set(tree.edges.map((edge) => edge.service)).size,
              ],
            ].map(([label, count]) => (
              <div
                key={label}
                className="rounded-xl border border-slate-200 bg-white p-4"
              >
                <div className="text-sm text-slate-500">{label}</div>
                <div className="mt-1 text-2xl font-bold text-slate-900">
                  {count}
                </div>
              </div>
            ))}
          </div>

          <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
            <div className="border-b border-slate-200 px-4 py-3">
              <h3 className="font-bold text-slate-900">Service graph</h3>
              <p className="text-sm text-slate-500">
                Follow the arrows between calls. Select a station to inspect
                its connections.
              </p>
            </div>
            <div className="overflow-auto bg-slate-50 p-4">
              {graphLayout && graphLayout.width > 0 && (
                <svg
                  aria-label="Interactive graph of train service calls"
                  className="mx-auto"
                  height={graphLayout.height}
                  role="group"
                  viewBox={`0 0 ${graphLayout.width} ${graphLayout.height}`}
                  width={graphLayout.width}
                >
                  <defs>
                    <marker
                      id="service-graph-arrow"
                      markerHeight="8"
                      markerWidth="8"
                      orient="auto"
                      refX="7"
                      refY="4"
                    >
                      <path d="M0,0 L8,4 L0,8 z" fill="#94a3b8" />
                    </marker>
                    <marker
                      id="service-graph-arrow-selected"
                      markerHeight="8"
                      markerWidth="8"
                      orient="auto"
                      refX="7"
                      refY="4"
                    >
                      <path d="M0,0 L8,4 L0,8 z" fill="#1d4ed8" />
                    </marker>
                  </defs>
                  {tree.edges.map((edge, index) => {
                    const source = graphLayout.positions.get(edge.source)
                    const target = graphLayout.positions.get(edge.target)
                    if (!source || !target) return null
                    const sameNode = edge.source === edge.target
                    const direction = target.x >= source.x ? 1 : -1
                    const edgeOffsets = edgePortOffsets.get(edge)
                    const startX =
                      source.x + (sameNode ? -graphNodeWidth / 3 : direction * graphNodeWidth / 2)
                    const endX =
                      target.x + (sameNode ? graphNodeWidth / 3 : -direction * graphNodeWidth / 2)
                    const startY = sameNode
                      ? source.y
                      : source.y + (edgeOffsets?.source ?? 0)
                    const endY = sameNode
                      ? target.y
                      : target.y + (edgeOffsets?.target ?? 0)
                    const middleX = (startX + endX) / 2
                    const verticalChange = endY - startY
                    const path = sameNode
                      ? `M ${startX} ${startY - graphNodeHeight / 3} C ${startX - 40} ${startY - 70}, ${endX + 40} ${endY - 70}, ${endX} ${endY - graphNodeHeight / 3}`
                      : `M ${startX} ${startY} C ${middleX} ${startY}, ${middleX} ${endY - verticalChange * 0.25}, ${endX} ${endY}`
                    const connected =
                      selectedNodeIds.includes(edge.source) ||
                      selectedNodeIds.includes(edge.target)
                    const highlighted =
                      selectedNodeIds.length === 0 || connected
                    return (
                      <g key={`${edge.source}-${edge.target}-${edge.service}-${index}`}>
                        <title>
                          {`Departure: ${formatTime(edge.plan_dep)} planned, ${formatTime(edge.act_dep)} actual. Arrival: ${formatTime(edge.plan_arr)} planned, ${formatTime(edge.act_arr)} actual.`}
                        </title>
                        <path
                          d={path}
                          fill="none"
                          markerEnd={
                            connected
                              ? "url(#service-graph-arrow-selected)"
                              : "url(#service-graph-arrow)"
                          }
                          opacity={highlighted ? 1 : 0.2}
                          stroke={connected ? "#1d4ed8" : "#94a3b8"}
                          strokeWidth={connected ? 2.5 : 1.5}
                        />
                      </g>
                    )
                  })}
                  {tree.nodes.map((node) => {
                    const position = graphLayout.positions.get(node.id)
                    if (!position) return null
                    const isSelected = selectedNodeIds.includes(node.id)
                    const arrivals = tree.edges
                      .filter((edge) => edge.target === node.id)
                    const departures = tree.edges.filter(
                      (edge) => edge.source === node.id,
                    )
                    return (
                      <g
                        key={node.id}
                        aria-label={`${nodeName(node)}${node.short_codes?.length ? `, ${node.short_codes.join(", ")}` : ""}`}
                        aria-pressed={isSelected}
                        className="cursor-pointer outline-none"
                        onClick={() => selectStationCalls(node)}
                        onKeyDown={(event) => {
                          if (event.key === "Enter" || event.key === " ") {
                            event.preventDefault()
                            selectStationCalls(node)
                          }
                        }}
                        role="button"
                        tabIndex={0}
                        transform={`translate(${position.x}, ${position.y})`}
                      >
                        <title>
                          {`${nodeName(node)}${node.short_codes?.length ? ` (${node.short_codes.join(", ")})` : ""}\nArrivals P/A: ${arrivals.map((edge) => `${formatTime(edge.plan_arr)}/${formatTime(edge.act_arr)}`).join(", ") || "—"}\nDepartures P/A: ${departures.map((edge) => `${formatTime(edge.plan_dep)}/${formatTime(edge.act_dep)}`).join(", ") || "—"}`}
                        </title>
                        <rect
                          fill={isSelected ? "#dbeafe" : "#ffffff"}
                          height={graphNodeHeight}
                          rx="12"
                          stroke={isSelected ? "#1d4ed8" : "#cbd5e1"}
                          strokeWidth={isSelected ? 2.5 : 1.25}
                          width={graphNodeWidth}
                          x={-graphNodeWidth / 2}
                          y={-graphNodeHeight / 2}
                        />
                        {arrivals.map((edge, index) => (
                          <text
                            key={`arrival-${edge.source}-${index}`}
                            fill="#1e3a8a"
                            fontSize="9"
                            textAnchor="start"
                            x={-graphNodeWidth / 2 + 8}
                            y={edgePortOffsets.get(edge)?.target ?? 0}
                          >
                            {`${formatTime(edge.plan_arr)} / ${formatTime(edge.act_arr)}`}
                          </text>
                        ))}
                        {departures.map((edge, index) => (
                          <text
                            key={`departure-${edge.target}-${index}`}
                            fill="#1e3a8a"
                            fontSize="9"
                            textAnchor="end"
                            x={graphNodeWidth / 2 - 8}
                            y={edgePortOffsets.get(edge)?.source ?? 0}
                          >
                            {`${formatTime(edge.plan_dep)} / ${formatTime(edge.act_dep)}`}
                          </text>
                        ))}
                        <text
                          fill="#0f172a"
                          fontSize="11"
                          fontWeight="600"
                          textAnchor="middle"
                          x="0"
                          y="-31"
                        >
                          {nodeName(node).slice(0, 16)}
                          {nodeName(node).length > 16 ? "…" : ""}
                        </text>
                        <text
                          fill="#64748b"
                          fontSize="8"
                          textAnchor="middle"
                          x="0"
                          y="-15"
                        >
                          {(node.short_codes ?? []).join(" · ") ||
                            node.services.join(", ").slice(0, 16)}
                        </text>
                      </g>
                    )
                  })}
                </svg>
              )}
            </div>
          </section>

          <div className="grid min-h-[32rem] gap-4 lg:grid-cols-[minmax(16rem,0.8fr)_minmax(0,1.8fr)]">
            <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
              <div className="border-b border-slate-200 p-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-bold text-slate-900">Stations</h3>
                  <span className="text-sm text-slate-500">
                    {visibleStationGroups.length} stations ·{" "}
                    {visibleStationGroups.reduce(
                      (count, group) => count + group.nodes.length,
                      0,
                    )}{" "}
                    calls
                  </span>
                </div>
                <input
                  type="search"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Filter stations or services"
                  aria-label="Filter stations or services"
                  className="mt-3 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-700 focus:ring-2 focus:ring-blue-100"
                />
              </div>
              <ul className="max-h-[36rem] divide-y divide-slate-100 overflow-y-auto">
                {visibleStationGroups.map((group) => (
                  <li key={group.key}>
                    <button
                      type="button"
                      onClick={() =>
                        setSelectedNodeIds(
                          sortCallsByTime(group.nodes, tree.edges).map(
                            (node) => node.id,
                          ),
                        )
                      }
                      aria-pressed={group.nodes.every((node) =>
                        selectedNodeIds.includes(node.id),
                      )}
                      aria-label={`Select ${group.location} station with all ${group.nodes.length} calls`}
                      className={`block w-full px-4 py-3 text-left transition ${group.nodes.every((node) =>
                        selectedNodeIds.includes(node.id),
                      )
                        ? "bg-blue-50"
                        : "hover:bg-slate-50"
                        }`}
                    >
                      <span className="block font-semibold text-slate-900">
                        {group.location}
                      </span>
                      <span className="mt-1 block text-xs text-slate-500">
                        {[...group.shortCodes].join(" · ") || "No station code"}
                      </span>
                      {group.nodes.length > 1 && (
                        <span className="mt-1 block text-xs text-slate-500">
                          {group.nodes.length} calls
                        </span>
                      )}
                    </button>
                  </li>
                ))}
                {visibleStationGroups.length === 0 && (
                  <li className="p-5 text-sm text-slate-500">
                    No stations match that filter.
                  </li>
                )}
              </ul>
            </section>

            <section className="space-y-4">
              {selectedNode ? (
                <>
                  <div className="rounded-2xl border border-slate-200 bg-white p-5">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <div className="text-sm font-medium text-blue-800">
                          Selected station
                        </div>
                        <h3 className="mt-1 text-2xl font-bold text-slate-950">
                          {nodeName(selectedNode)}
                        </h3>
                        <p className="mt-1 text-sm text-slate-500">
                          {(selectedNode.short_codes ?? []).join(" · ") ||
                            "No station code"}
                        </p>
                        {selectedNodes.length > 1 && (
                          <p className="mt-1 text-sm text-slate-600">
                            {selectedNodes.length} calls at this station
                          </p>
                        )}
                      </div>
                      {!selectedNodeIds.includes(tree.root) && (
                        <button
                          type="button"
                          onClick={selectRoot}
                          className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                        >
                          Back to root
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="space-y-4">
                    {selectedCallGroups.map(
                      ({ node, arrivals, departures }, index) => (
                        <section
                          key={node.id}
                          className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
                        >
                          <div className="mb-3 flex flex-wrap items-center gap-2">
                            {selectedCallGroups.length > 1 && (
                              <span className="text-sm font-semibold text-slate-700">
                                Call {index + 1}
                              </span>
                            )}
                          </div>
                          <div className="grid gap-4 sm:grid-cols-2">
                            <div className="space-y-2">
                              <h4 className="text-sm font-semibold text-slate-700">
                                Arrives from
                              </h4>
                              {arrivals.length ? (
                                arrivals.map((edge) => (
                                  <RelationCard
                                    key={`${edge.source}-${edge.target}-${edge.service}`}
                                    edge={edge}
                                    neighbor={nodesById.get(edge.source)}
                                    direction="arrival"
                                    onSelect={() => {
                                      const source = nodesById.get(edge.source)
                                      if (source) selectStationCalls(source)
                                    }}
                                  />
                                ))
                              ) : (
                                <p className="rounded-xl bg-white p-3 text-sm text-slate-500">
                                  No incoming calls.
                                </p>
                              )}
                            </div>
                            <div className="space-y-2">
                              <h4 className="text-sm font-semibold text-slate-700">
                                Continues to
                              </h4>
                              {departures.length ? (
                                departures.map((edge) => (
                                  <RelationCard
                                    key={`${edge.source}-${edge.target}-${edge.service}`}
                                    edge={edge}
                                    neighbor={nodesById.get(edge.target)}
                                    direction="departure"
                                    onSelect={() => {
                                      const target = nodesById.get(edge.target)
                                      if (target) selectStationCalls(target)
                                    }}
                                  />
                                ))
                              ) : (
                                <p className="rounded-xl bg-white p-3 text-sm text-slate-500">
                                  No outgoing calls.
                                </p>
                              )}
                            </div>
                          </div>
                        </section>
                      ),
                    )}
                  </div>
                </>
              ) : (
                <div className="rounded-2xl border border-dashed border-slate-300 p-8 text-center text-slate-500">
                  Select a station to inspect its service links.
                </div>
              )}
            </section>
          </div>
        </>
      )}
    </div>
  )
}
