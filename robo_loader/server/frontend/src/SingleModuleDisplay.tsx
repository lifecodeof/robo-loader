import { useMemo } from "react"
import { useAIImage } from "./hooks/useAIImage"
import type { Status } from "./types"

export default function SingleModuleDisplay({ status }: { status: Status }) {
  const aiImage = useAIImage(status.author)
  const photoUrl = useMemo(() => {
    const url = new URL("/api/photo.png", window.location.origin)
    url.searchParams.set("module_name", status.module_name)
    return url.toString()
  }, [status.module_name])

  return (
    <div className="card card-side bg-base-100 ai-card w-full my-4">
      <figure>
        <img src={aiImage} className="h-80 w-60" />
      </figure>
      <div className="card-body basis-0 text-start">
        <h2 className="card-title">{status.author}</h2>
        <h2 className="card-title !text-lg">{status.title}</h2>
        <p>{status.content}</p>
      </div>
      <figure>
        <img src={photoUrl} className="h-80 w-60" />
      </figure>
    </div>
  )
}
