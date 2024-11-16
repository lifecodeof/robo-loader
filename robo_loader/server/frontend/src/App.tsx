import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { StatusGrid } from "./StatusGrid"
import { useState } from "react"
import { TerminalView } from "./TerminalView"
import { ValuePanel } from "./ValuePanel"

function App() {
  const [queryClient] = useState(() => new QueryClient())

  return (
    <main>
      <QueryClientProvider client={queryClient}>
        <ValuePanel />
        <StatusGrid />
        <TerminalView />
      </QueryClientProvider>
    </main>
  )
}

export default App
