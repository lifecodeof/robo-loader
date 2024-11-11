import { useQuery } from "@tanstack/react-query"
import type { Data } from "./types"
import { useLayoutEffect, useRef, useState } from "react"

export function StatusGrid() {
  const query = useQuery({
    queryKey: ["statuses"],
    queryFn: async () => {
      const response = await fetch("/api/statuses")
      return (await response.json()) as Record<string, Data>
    },
    refetchInterval: 1000,
  })

  return (
    <div className="">
      {query.isLoading && "Yükleniyor..."}
      <div className="my-grid">
        {query.data &&
          Object.values(query.data).map((status) => (
            <DynamicSized key={status.author}>
              <div className="border-2 p-2 m-1 w-min h-min overflow-hidden">
                <div className="inline-block max-w-80 truncate font-bold">
                  {status.author}
                </div>
                <div className="inline-block max-w-80 truncate ml-2">
                  {status.title}
                </div>
                <pre>{status.content.trim()}</pre>
              </div>
            </DynamicSized>
          ))}
      </div>
    </div>
  )
}

const CELL_SIZE = 10
function DynamicSized({ children }: { children: React.ReactNode }) {
  const ref = useRef<HTMLDivElement>(null)
  // const [style, setStyle] = useState<React.CSSProperties>({})

  // const prevWidth = useRef(0)
  // const prevHeight = useRef(0)
  // const prevStyle = useRef<React.CSSProperties>(style)

  const width = ref.current?.scrollWidth || 0
  const height = ref.current?.scrollHeight || 0

  // const isWidthChanged = prevWidth.current !== width
  // const isHeightChanged = prevHeight.current !== height
  // const isStyleChanged = prevStyle.current !== style

  // prevWidth.current = width
  // prevHeight.current = height
  // prevStyle.current = style

  // console.log(isStyleChanged)

  // if (!isStyleChanged && (isWidthChanged || isHeightChanged)) {
  //   setStyle({
  //     gridRow: `span ${Math.ceil(width / CELL_SIZE)}`,
  //     gridColumn: `span ${Math.ceil(height / CELL_SIZE)}`,
  //   })
  // }

  // const rowSpan = Math.ceil(height / CELL_SIZE)
  // const colSpan = Math.ceil(width / CELL_SIZE)

  // setStyle({ gridRow: `span ${rowSpan}`, gridColumn: `span ${colSpan}` })

  const style = {
    gridRow: `span ${Math.ceil(height / CELL_SIZE)}`,
    gridColumn: `span ${Math.ceil(width / CELL_SIZE)}`,
  }

  return (
    <div ref={ref} style={style} className="w-min h-min">
      {children}
    </div>
  )
}
