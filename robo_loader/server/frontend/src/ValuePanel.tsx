import { useMutation } from "@tanstack/react-query"
import { useEffect, useState } from "react"

const LABELS = [
  "Sıcaklık",
  "Nem",
  "Işık",
  "Mesafe",
  "Nabız",
  "Hava Kalitesi",
  "Gaz",
  "Titreşim",
  "Yağmur",
  "Yakınlık",
] as const

export const ValuePanel = () => {
  const [variables, setVariables] = useState({
    Sıcaklık: 0,
    Nem: 0,
    Işık: 0,
    Mesafe: 0,
    Nabız: 0,
    "Hava Kalitesi": 0,
    Gaz: 0,
    Titreşim: 0,
    Yağmur: 0,
    Yakınlık: 0,
  })

  const setVariable = (key: string, value: string) => {
    setVariables((prev) => ({ ...prev, [key]: value }))
  }

  const mutation = useMutation<void, unknown, typeof variables>({
    mutationFn: async (variables) => {
      await fetch("/api/set_data", {
        method: "POST",
        body: JSON.stringify(variables),
      })
    },
  })

  useEffect(() => {
    mutation.mutate(variables)
  }, [variables])

  return (
    <table className="mb-4">
      {LABELS.map((label) => (
        <tr key={label}>
          <td>
            <label>{label}</label>
          </td>
          <td>
            <input
              type="number"
              value={variables[label]}
              onChange={(e) => setVariable(label, e.target.value)}
            />
          </td>
        </tr>
      ))}
    </table>
  )
}
