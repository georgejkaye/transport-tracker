export const getDelayString = (delay: number) =>
  delay == null ? "-" : delay > 0 ? `+${delay}` : `${delay}`
