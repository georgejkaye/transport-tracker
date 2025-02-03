import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import Link from "next/link"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Train Journey Tracker",
  description: "Keep track of train journeys",
}

const TopBar = () => (
  <div className="bg-accent p-4">
    <Link href={"/"}>
      <h1 className="font-bold text-2xl text-white">Train Journey Tracker</h1>
    </Link>
  </div>
)

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <TopBar />
        <main className="items-center flex flex-col justify-between p-4 flex">
          <div className="w-full lg:w-[64rem]">{children}</div>
        </main>
        <link
          href="https://unpkg.com/maplibre-gl@4.7.0/dist/maplibre-gl.css"
          rel="stylesheet"
        />
      </body>
    </html>
  )
}
