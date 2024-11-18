import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useState } from "react"

function App() {
  const [queryClient] = useState(() => new QueryClient())

  return (
    <main>
      <QueryClientProvider client={queryClient}>
      </QueryClientProvider>
    </main>
  )
}

export default App
