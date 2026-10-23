export const isNumber = (input: string) =>
  input != null && input !== "" && !isNaN(Number(input))
