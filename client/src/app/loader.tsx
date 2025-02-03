import { ColorRing } from "react-loader-spinner"

export const Loader = () => (
  <div className="flex mx-auto w-full justify-center">
    <ColorRing
      height={80}
      width={80}
      colors={["#003366", "#003366", "#003366", "#003366", "#003366"]}
    />
  </div>
)
