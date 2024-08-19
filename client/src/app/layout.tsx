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
        <main className="items-center flex flex-col justify-between py-4 px-4 lg:px-0">
          {children}
        </main>
      </body>
    </html>
  )
}
