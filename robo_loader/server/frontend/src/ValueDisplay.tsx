import { useValues } from "./hooks/apiClient"
import Marquee from "react-fast-marquee"

export default function ValueDisplay() {
  const values = useValues()

  return (
    <Marquee className="justify-between mb-8">
      {values.data &&
        Object.entries(values.data).map(([key, value]) => (
          <div key={key} className="mx-10">
            <Gauge />
            {key}: {value}
          </div>
        ))}
    </Marquee>
  )
}

const Gauge = () => <img src="/gauge.png" className="size-7 inline mr-2" />
