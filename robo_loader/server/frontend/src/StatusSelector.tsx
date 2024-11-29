import { useEffect, useState } from "react"
import Alert from "./components/Alert"
import { useAllModules, useMAMapping, useStatuses } from "./hooks/apiClient"
import SingleModuleDisplay from "./SingleModuleDisplay"
import { useMutation } from "@tanstack/react-query"

const EVERYONE = "Herkes"

export default function StatusSelector() {
  const statusesQuery = useStatuses()
  const allModules = useAllModules()
  const maMapping = useMAMapping()

  const [selectedModule, setSelectedModule] = useState<string>(EVERYONE)

  const changeModule = useMutation({
    mutationFn: async (module_name: string) => {
      await fetch("/api/change_module", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ module_name }),
      })
    },
  })

  useEffect(() => {
    changeModule.mutate(selectedModule)
  }, [selectedModule])

  const statuses =
    statusesQuery.data && Object.values(statusesQuery.data).flat()

  return (
    <div>
      <select
        className="select w-full max-w-xs select-bordered"
        value={selectedModule}
        onChange={(e) => setSelectedModule(e.target.value)}
      >
        <option value={EVERYONE}>Herkes</option>
        {allModules.isLoading && <option>Yükleniyor...</option>}
        {allModules.data?.map((module) => (
          <option key={module} value={module}>
            {maMapping[module] ?? module}
          </option>
        ))}
      </select>

      {statusesQuery.isLoading && (
        <div>
          <span className="loading loading-bars loading-lg"></span>
          Yükleniyor...
        </div>
      )}
      {statusesQuery.isError && (
        <Alert>Hata oluştu: {statusesQuery.error.message}</Alert>
      )}
      {statuses && selectedModule && !statuses?.length && (
        <Alert>Seçtiğiniz kişi durum belirtmemiş</Alert>
      )}
      <div className="flex flex-col justify-center items-stretch gap-4 max-w-screen-lg mx-auto my-6">
        {statuses?.map((status) => (
          <SingleModuleDisplay key={status.author} status={status} />
        ))}
      </div>
    </div>
  )
}
