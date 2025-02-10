"use client"

import Link from "next/link"
import { linkStyle } from "./styles"

const YearLink = (props: { year: number }) => (
  <Link className="cursor-pointer" href={`/train/years/${props.year}`}>
    <div className="p-4 text-xl rounded bg-blue-400">{props.year}</div>
  </Link>
)

const Page = () => {
  return (
    <div>
      <h1 className="text-xl font-bold mb-2">Years</h1>
      <div className="flex flex-row flex-wrap gap-4">
        <YearLink year={2025} />
        <YearLink year={2024} />
        <YearLink year={2023} />
        <YearLink year={2022} />
        <YearLink year={2021} />
        <YearLink year={2020} />
        <YearLink year={2019} />
      </div>
    </div>
  )
}

export default Page
