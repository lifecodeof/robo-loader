import Alert from "./components/Alert"
import { useInfo, useMAMapping, useRunningModules } from "./hooks/apiClient"

export default function RunningModules() {
  const runningModules = useRunningModules()
  const maMapping = useMAMapping()
  const info = useInfo()

  const authors = runningModules.data?.map((m) => maMapping[m] ?? m) ?? []

  return (
    <div>
      {runningModules.isLoading && (
        <div>
          <span className="loading loading-bars loading-lg"></span>
          Yükleniyor...
        </div>
      )}

      {runningModules.isError && (
        <Alert>Hata oluştu: {runningModules.error.message}</Alert>
      )}

      <div className="flex flex-wrap gap-4 m-4 pt-8">
        {runningModules.data?.map((module) => (
          <div role="alert" className="alert alert-info w-max">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              className="h-6 w-6 shrink-0 stroke-current"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              ></path>
            </svg>
            <span>
              {maMapping[module] ?? module}:{" "}
              {info.data?.[module] ?? "Çalışıyor?"}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
