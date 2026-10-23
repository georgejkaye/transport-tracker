const mileageToMilesAndChains = (miles: number) => ({
  miles: Math.floor(miles),
  chains: (miles * 80) % 80,
})

export const getMilesAndChainsStringFromString = (mileage: string) =>
  getMilesAndChainsStringFromNumber(Number(mileage))

export const getMilesAndChainsStringFromNumber = (mileage: number) => {
  let { miles, chains } = mileageToMilesAndChains(mileage)
  return `${miles}m ${Math.round(chains)}ch`
}
