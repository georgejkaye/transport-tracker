export const getLongDate = (dateString: string) => {
  let date = new Date(Date.parse(dateString))
  return date.toLocaleString("en-GB", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  })
}

export const getShortDate = (dateString: string) => {
  let date = new Date(Date.parse(dateString))
  return date.toLocaleString("en-GB", {
    day: "numeric",
    month: "numeric",
    year: "2-digit",
  })
}
