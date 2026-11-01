import TrainServiceGraphPage from "../../page"

export default async function TrainServiceGraphRoute({
  params,
}: {
  params: Promise<{ identity: string; departureDate: string }>
}) {
  const { identity, departureDate } = await params
  return (
    <TrainServiceGraphPage
      initialDepartureDate={departureDate}
      initialIdentity={identity}
    />
  )
}
