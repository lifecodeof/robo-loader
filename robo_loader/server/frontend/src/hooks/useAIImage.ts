import { useEffect, useState } from "react"

let globalIndex = 0
const maxIndex = 3

const cachedIndexes: Record<string, number> = {}

export const useAIImage = (seed?: string) => {
  const [index, setIndex] = useState<number>()

  useEffect(() => {
    if (seed && cachedIndexes[seed]) {
      setIndex(cachedIndexes[seed])
      return
    }

    globalIndex++
    if (globalIndex > maxIndex) {
      globalIndex = 0
    }

    if (seed) cachedIndexes[seed] = globalIndex
    setIndex(globalIndex)
  }, [seed])

  return `/ai-images/${index}.png`
}
