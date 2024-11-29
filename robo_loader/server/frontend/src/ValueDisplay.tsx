import { useEffect, useState } from "react"
import { useValues } from "./hooks/apiClient"
import Marquee from "react-fast-marquee"

export default function ValueDisplay() {
  const wd = useWindowDimensions()
  const values = useValues()

  const itemWidth = !values.data
    ? 0
    : wd.width / Object.keys(values.data).length

  return (
    <Marquee className="justify-between mb-8">
      {values.data &&
        Object.entries(values.data).map(([key, value]) => (
          <div
            style={{
              width: `${itemWidth}px`,
            }}
          >
            <div key={key} className="mx-auto">
              <Gauge />
              {key}: {value}
            </div>
          </div>
        ))}
    </Marquee>
  )
}

const Gauge = () => <img src="/gauge.png" className="size-7 inline mr-2" />

function getWindowDimensions() {
  const width = window.innerWidth
  const height = window.innerHeight

  return {
    width,
    height,
  }
}

function useWindowDimensions() {
  const [windowDimensions, setWindowDimensions] = useState(
    getWindowDimensions()
  )

  useEffect(() => {
    function handleResize() {
      setWindowDimensions(getWindowDimensions())
    }

    window.addEventListener("resize", handleResize)
    return () => window.removeEventListener("resize", handleResize)
  }, [])

  return windowDimensions
}
