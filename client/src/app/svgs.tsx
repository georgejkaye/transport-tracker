export const StartTerminusSymbol = (props: { lineColour: string }) => {
  let { lineColour } = props
  return (
    <svg width={32} height={32}>
      <path
        fill="none"
        stroke={lineColour}
        stroke-width="4"
        stroke-dasharray="none"
        d="M 16 16 L 16 40"
      />
      <ellipse
        fill="#ffffff"
        stroke={lineColour}
        stroke-width="4"
        cx="16"
        cy="16"
        rx="8"
        ry="8"
      />
    </svg>
  )
}

export const EndTerminusSymbol = (props: { lineColour: string }) => {
  let { lineColour } = props
  return (
    <svg width={32} height={32}>
      <path
        fill="none"
        stroke={lineColour}
        stroke-width="4"
        stroke-dasharray="none"
        d="M 16 0 L 16 16"
      />
      <ellipse
        fill="#ffffff"
        stroke={lineColour}
        stroke-width="4"
        cx="16"
        cy="16"
        rx="8"
        ry="8"
      />
    </svg>
  )
}

export const StationSymbol = (props: { lineColour: string }) => {
  let { lineColour } = props
  return (
    <svg width={32} height={50}>
      <path
        fill="none"
        stroke={lineColour}
        stroke-width="4"
        stroke-dasharray="none"
        d="M 16 0 L 16 50"
      />
      <ellipse
        fill="#ffffff"
        stroke={lineColour}
        stroke-width="4"
        cx="16"
        cy="25"
        rx="6"
        ry="6"
      />
    </svg>
  )
}

export const LineDashed = (props: { lineColour: string }) => {
  let { lineColour } = props
  return (
    <svg width={32} height={32}>
      <path
        fill="none"
        stroke={lineColour}
        stroke-width="4"
        stroke-dasharray="4 4"
        d="M 16 0 L 16 32"
      />
    </svg>
  )
}

export const LineSolid = (props: { lineColour: string }) => {
  let { lineColour } = props
  return (
    <svg width={20} height={10}>
      <path
        fill="none"
        stroke={lineColour}
        stroke-width="2"
        stroke-dasharray="0"
        d="m 10 0 v10 20"
      />
    </svg>
  )
}
