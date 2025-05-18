"use client"

import Link from "next/link"
import { linkStyle } from "../../styles"

const YearLink = (props: { userId: number; year: number }) => (
  <Link
    className="cursor-pointer"
    href={`/users/${props.userId}/train/legs/years/${props.year}`}
  >
    <div className="p-4 text-xl rounded bg-blue-400">{props.year}</div>
  </Link>
)

const Page = ({ params }: { params: { userId: string } }) => {
  const { userId } = params
  const userIdNumber = parseInt(userId)
  return (
    <div>
      <h1 className="text-xl font-bold mb-2">Years</h1>
      <div className="flex flex-row flex-wrap gap-4">
        <YearLink userId={userIdNumber} year={2025} />
        <YearLink userId={userIdNumber} year={2024} />
        <YearLink userId={userIdNumber} year={2023} />
        <YearLink userId={userIdNumber} year={2022} />
        <YearLink userId={userIdNumber} year={2021} />
        <YearLink userId={userIdNumber} year={2020} />
        <YearLink userId={userIdNumber} year={2019} />
      </div>
    </div>
  )
}

export default Page
