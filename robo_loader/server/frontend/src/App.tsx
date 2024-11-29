import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useState } from "react"
import SingleModuleDisplay from "./SingleModuleDisplay"
import StatusSelector from "./StatusSelector"
import ValueDisplay from "./ValueDisplay"
import RunningModules from "./RunningModules"

function App() {
  const [queryClient] = useState(() => new QueryClient())

  return (
    <main className="text-center mx-auto mt-6">
      <QueryClientProvider client={queryClient}>
        <ValueDisplay />
        <StatusSelector />
        <RunningModules />
      </QueryClientProvider>
    </main>
  )
}

export default App
