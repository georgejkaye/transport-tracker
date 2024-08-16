import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Train Journey Tracker",
  description: "Keep track of train journeys",
}

const TopBar = () => (
  <div className="bg-accent p-4 mb-4">
    <h1 className="font-bold text-2xl">Train Journey Tracker</h1>
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
        <main className="min-h-screen items-center flex flex-col justify-between py-4 px-2 lg:px-0">
          {children}
        </main>
      </body>
    </html>
  )
}
