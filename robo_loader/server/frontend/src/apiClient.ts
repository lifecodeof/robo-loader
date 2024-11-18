import type { Data } from "./types"
import { useQuery } from "@tanstack/react-query"

export const useApiQuery = <T = any>(url: string) =>
  useQuery<T>({
    queryKey: [url],
    queryFn: async () => {
      const response = await fetch("/api/" + url)
      return await response.json()
    },
    refetchInterval: 1000,
    retry: false,
  })

export const useStatuses = () => useApiQuery<Record<string, Data>>("statuses")
export const useValues = () => useApiQuery<Record<string, number>>("values")
