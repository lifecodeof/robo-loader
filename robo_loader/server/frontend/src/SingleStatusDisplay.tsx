import { useAIImage } from "./hooks/useAIImage"
import type { Status } from "./types"

export default function SingleStatusDisplay({ status }: { status: Status }) {
  const aiImage = useAIImage(status.author)
  
  return (
    <div className="card card-side bg-base-100 ai-card w-max">
      <figure>
        <img src={aiImage} className="h-80 w-60" />
      </figure>
      <div className="card-body min-w-[30rem] text-start">
        <h2 className="card-title">{status.author}</h2>
        <h2 className="card-title !text-lg">{status.title}</h2>
        <p>{status.content}</p>
      </div>
    </div>
  )
}
