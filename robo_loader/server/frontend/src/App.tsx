import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useState } from "react"
import SingleStatusDisplay from "./SingleStatusDisplay"
import StatusSelector from "./StatusSelector"
import ValueDisplay from "./ValueDisplay"

function App() {
  const [queryClient] = useState(() => new QueryClient())

  return (
    <main className="text-center mx-auto mt-6">
      <QueryClientProvider client={queryClient}>
        <ValueDisplay />
        <StatusSelector />
      </QueryClientProvider>
    </main>
  )
}

export default App
