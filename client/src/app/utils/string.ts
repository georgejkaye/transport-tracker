export const truncateString = (input: string, length: number) =>
  input.length <= length ? input : `${input.substring(0, length)}...`
