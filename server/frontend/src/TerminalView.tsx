import { useQuery } from "@tanstack/react-query"
import type { Data } from "./types"

export function TerminalView() {
  const query = useQuery({
    queryKey: ["messages"],
    queryFn: async () => {
      const response = await fetch("/api/messages")
      const data = (await response.json()) as Data[]
      return data.reverse()
    },
    refetchInterval: 1500,
  })

  return (
    <div>
      {query.isLoading && "Loading..."}
      <div className="silkscreen-regular w-full p-4">
        {query.data &&
          query.data.map((message, i) => (
            <div key={i}>
              <div>
                <span className="silkscreen-bold mr-2">{message.author}:</span>
                <span>{message.content}</span>
              </div>
            </div>
          ))}
      </div>
    </div>
  )
}
