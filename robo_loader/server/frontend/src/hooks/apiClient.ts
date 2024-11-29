import type { Status } from "../types"
import { useQuery } from "@tanstack/react-query"

export const useApiQuery = <T = any>(url: string, continuous: boolean = true) =>
  useQuery<T>({
    queryKey: [url],
    queryFn: async () => {
      const response = await fetch("/api/" + url)
      return await response.json()
    },
    refetchInterval: continuous ? 1000 : false,
    retry: continuous ? false : 3,
  })

export const useStatuses = () => useApiQuery<Status[]>("statuses")
export const useRunningModules = () => useApiQuery<string[]>("running_modules")
export const useValues = () => useApiQuery<Record<string, number>>("values")
export const useInfo = () => useApiQuery<Record<string, string>>("info")
export const useAllModules = () => useApiQuery<string[]>("all_modules", false)

export const useMAMapping = () => {
  const query = useApiQuery<string[]>("module_author_mapping", false)
  return query.data ?? {}
}
