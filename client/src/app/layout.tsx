import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import Link from "next/link"
import { ReactQueryClientProvider } from "./api/ReactQueryClientProvider"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Transport tracker",
  description: "Keep track of public transport journeys",
}

const TopBar = () => (
  <div className="bg-accent flex items-center justify-between p-4">
    <Link href={"/"}>
      <h1 className="font-bold text-xl text-white sm:text-2xl">
        Transport Tracker
      </h1>
    </Link>
    <Link
      href="/tree"
      className="whitespace-nowrap rounded border border-white/50 px-2 py-2 text-xs text-white hover:bg-white/10 sm:px-3 sm:text-sm"
    >
      Service graph explorer
    </Link>
  </div>
)

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <ReactQueryClientProvider>
      <html lang="en">
        <body className={inter.className}>
          <TopBar />
          <main className="items-center flex flex-col justify-between p-4 flex">
            <div className="w-full lg:max-w-[92rem]">{children}</div>
          </main>
          <link
            href="https://unpkg.com/maplibre-gl@4.7.0/dist/maplibre-gl.css"
            rel="stylesheet"
          />
        </body>
      </html>
    </ReactQueryClientProvider>
  )
}
