import type { Config } from "tailwindcss"

const buffer = 50
const minDesktopSize = 1000
const minTabletSize = 600
const contentSize = minDesktopSize - buffer
const tabletContentSize = minTabletSize - buffer
const mobileContentSize = 350

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      width: {
        desktop: `${contentSize}px`,
        tablet: `${tabletContentSize}px`,
        mobile: `${mobileContentSize}px`,
      },
      colors: {
        accent: "#003366",
      },
    },
  },
  plugins: [],
}
export default config
