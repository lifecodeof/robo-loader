import { useMemo, useState } from "react"
import { useStatuses } from "./hooks/apiClient"
import SingleStatusDisplay from "./SingleStatusDisplay"
import Alert from "./components/Alert"

const EVERYONE = "Herkes"

export default function StatusSelector() {
  const statuses = useStatuses()
  const [selectedAuthor, setSelectedAuthor] = useState<string>(EVERYONE)
  const selectedStatuses =
    selectedAuthor === EVERYONE
      ? statuses.data
      : statuses.data?.filter((s) => s.author === selectedAuthor)

  return (
    <div>
      <select
        className="select w-full max-w-xs select-bordered"
        value={selectedAuthor}
        onChange={(e) => setSelectedAuthor(e.target.value)}
      >
        <option value={EVERYONE}>Herkes</option>
        {statuses.data &&
          statuses.data.map((status) => (
            <option key={status.author} value={status.author}>
              {status.author}
            </option>
          ))}
      </select>

      {statuses.isLoading && (
        <div>
          <span className="loading loading-bars loading-lg"></span>
          Yükleniyor...
        </div>
      )}
      {statuses.isError && <Alert>Hata oluştu: {statuses.error.message}</Alert>}
      {statuses.data && selectedAuthor && !selectedStatuses.length && (
        <Alert>Seçtiğiniz kişi durum belirtmemiş</Alert>
      )}
      <div className="flex flex-wrap justify-center gap-4 w-full mx-auto my-6">
        {selectedStatuses?.map((status) => (
          <SingleStatusDisplay key={status.author} status={status} />
        ))}
      </div>
    </div>
  )
}
