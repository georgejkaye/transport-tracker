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

export const getLongDateAndTime = (dateString: string) => {
  let date = new Date(Date.parse(dateString))
  let weekdayFormatString = date.toLocaleString("en-GB", {
    weekday: "long",
  })
  let dateFormatString = date.toLocaleString("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
  })
  let timeFormatString = date.toLocaleString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
  })
  return `${weekdayFormatString} ${dateFormatString}, ${timeFormatString}`
}
