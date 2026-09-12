import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { ImageIcon, UploadIcon } from "lucide-react"
import { toast } from "sonner"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty"
import { Field, FieldLabel } from "@/components/ui/field"
import {
  InputGroup,
  InputGroupAddon,
  InputGroupButton,
  InputGroupTextarea,
} from "@/components/ui/input-group"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
import { Spinner } from "@/components/ui/spinner"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import {
  addPhotoVersion,
  createPhoto,
  latestImageUrl,
  listPhotos,
  logout,
  queryKeys,
  type Photo,
  type Profile,
} from "@/lib/api"
import { cn } from "@/lib/utils"
import { PRESETS } from "@/presets"

const ACCEPT = "image/jpeg,image/png,image/webp"

type StudioProps = {
  profile: Profile
}

export function Studio({ profile }: StudioProps) {
  const queryClient = useQueryClient()
  const [prompt, setPrompt] = useState(PRESETS[0].prompt)
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [dragging, setDragging] = useState(false)

  const photos = useQuery({
    queryKey: queryKeys.photos,
    queryFn: listPhotos,
  })

  const selected = photos.data?.find((photo) => photo.id === selectedId) ?? null
  const selectedPreset = PRESETS.find((preset) => preset.prompt === prompt)?.id ?? ""
  const sourceUrl = selected ? latestImageUrl(selected) : previewUrl

  const signOut = useMutation({
    mutationFn: logout,
    onSuccess: () => {
      queryClient.setQueryData(queryKeys.profile, null)
      queryClient.removeQueries({ queryKey: queryKeys.photos })
      toast.success("Signed out")
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : "Could not sign out")
    },
  })

  const generate = useMutation({
    mutationFn: async () => {
      const text = prompt.trim()
      if (!text) {
        throw new Error("Write a prompt first")
      }
      if (selected) {
        return addPhotoVersion(selected.id, text)
      }
      if (!file) {
        throw new Error("Drop a photo first")
      }
      return createPhoto({ prompt: text, image: file })
    },
    onSuccess: (photo) => {
      queryClient.setQueryData(queryKeys.photos, (current: Photo[] | undefined) => {
        const rest = (current ?? []).filter((item) => item.id !== photo.id)
        return [photo, ...rest]
      })
      setSelectedId(photo.id)
      toast.success(selected ? "New version ready" : "Edit ready")
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : "Edit failed")
    },
  })

  function takeFile(next: File) {
    if (!ACCEPT.split(",").includes(next.type)) {
      toast.error("Use a jpeg, png, or webp image")
      return
    }
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
    }
    setFile(next)
    setPreviewUrl(URL.createObjectURL(next))
    setSelectedId(null)
  }

  return (
    <div className="flex min-h-[100dvh] flex-col">
      <header className="flex items-center justify-between gap-4 border-b px-4 py-3 md:px-8">
        <div className="flex flex-col gap-1">
          <p className="text-xs tracking-[0.28em] text-primary uppercase">Photogen</p>
          <p className="text-sm text-muted-foreground">
            Signed in as <span className="text-foreground">{profile.username}</span>
          </p>
        </div>
        <Button variant="outline" onClick={() => signOut.mutate()} disabled={signOut.isPending}>
          {signOut.isPending ? <Spinner data-icon="inline-start" /> : null}
          Sign out
        </Button>
      </header>

      <main className="mx-auto grid w-full max-w-[1400px] flex-1 grid-cols-1 gap-8 px-4 py-6 md:px-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)]">
        <section className="flex flex-col gap-5">
          <div className="flex flex-col gap-2">
            <h1 className="font-heading text-2xl tracking-tight">Studio</h1>
            <p className="text-sm text-muted-foreground">
              {selected
                ? "A gallery photo is selected. Generate appends a new version."
                : "Drop a new original, pick a look, then generate."}
            </p>
          </div>

          <label
            className={cn(
              "relative flex min-h-72 cursor-pointer flex-col overflow-hidden rounded-xl ring-1 ring-foreground/10 transition-transform duration-150 ease-out",
              dragging ? "ring-primary" : null
            )}
            onDragOver={(event) => {
              event.preventDefault()
              setDragging(true)
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(event) => {
              event.preventDefault()
              setDragging(false)
              const next = event.dataTransfer.files[0]
              if (next) {
                takeFile(next)
              }
            }}
          >
            <input
              type="file"
              accept={ACCEPT}
              className="sr-only"
              onChange={(event) => {
                const next = event.target.files?.[0]
                if (next) {
                  takeFile(next)
                }
              }}
            />
            {sourceUrl ? (
              <img src={sourceUrl} alt="Current source" className="size-full object-cover" />
            ) : (
              <div className="flex flex-1 flex-col items-center justify-center gap-3 bg-card px-6 text-center">
                <UploadIcon className="size-8 text-primary" />
                <p className="font-medium">Drop a photo here</p>
                <p className="text-sm text-muted-foreground">jpeg, png, or webp. 10MB max.</p>
              </div>
            )}
          </label>

          <Field>
            <FieldLabel>Looks</FieldLabel>
            <ToggleGroup
              type="single"
              value={selectedPreset}
              onValueChange={(value) => {
                const preset = PRESETS.find((item) => item.id === value)
                if (preset) {
                  setPrompt(preset.prompt)
                }
              }}
              spacing={2}
              variant="outline"
              className="flex-wrap"
            >
              {PRESETS.map((preset) => (
                <ToggleGroupItem key={preset.id} value={preset.id}>
                  {preset.label}
                </ToggleGroupItem>
              ))}
            </ToggleGroup>
          </Field>

          <Field>
            <FieldLabel htmlFor="prompt">Prompt</FieldLabel>
            <InputGroup className="h-auto">
              <InputGroupTextarea
                id="prompt"
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
                rows={4}
                maxLength={500}
              />
              <InputGroupAddon align="block-end">
                <InputGroupButton
                  variant="default"
                  size="sm"
                  onClick={() => generate.mutate()}
                  disabled={generate.isPending}
                >
                  {generate.isPending ? <Spinner data-icon="inline-start" /> : null}
                  {selected ? "Refine" : "Generate"}
                </InputGroupButton>
              </InputGroupAddon>
            </InputGroup>
          </Field>
        </section>

        <section className="flex flex-col gap-5">
          <div className="flex items-end justify-between gap-3">
            <div className="flex flex-col gap-1">
              <h2 className="font-heading text-xl tracking-tight">Gallery</h2>
              <p className="text-sm text-muted-foreground">Original plus every generated version.</p>
            </div>
            {selected ? (
              <Button variant="ghost" size="sm" onClick={() => setSelectedId(null)}>
                New original
              </Button>
            ) : null}
          </div>
          <Separator />
          <Gallery photos={photos.data} isPending={photos.isPending} isError={photos.isError} selectedId={selectedId} onSelect={setSelectedId} />
        </section>
      </main>
    </div>
  )
}

function Gallery({
  photos,
  isPending,
  isError,
  selectedId,
  onSelect,
}: {
  photos: Photo[] | undefined
  isPending: boolean
  isError: boolean
  selectedId: number | null
  onSelect: (id: number) => void
}) {
  if (isPending) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Skeleton className="h-64" />
        <Skeleton className="h-64" />
      </div>
    )
  }
  if (isError) {
    return (
      <Empty className="border">
        <EmptyHeader>
          <EmptyTitle>Gallery failed to load</EmptyTitle>
          <EmptyDescription>Sign in again if the session expired.</EmptyDescription>
        </EmptyHeader>
      </Empty>
    )
  }
  if (!photos?.length) {
    return (
      <Empty className="border border-dashed">
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <ImageIcon />
          </EmptyMedia>
          <EmptyTitle>No photos yet</EmptyTitle>
          <EmptyDescription>Drop an original on the left and generate a first edit.</EmptyDescription>
        </EmptyHeader>
      </Empty>
    )
  }

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
      {photos.map((photo) => (
        <Card
          key={photo.id}
          size="sm"
          className={cn(
            "cursor-pointer transition-transform duration-150 ease-out active:scale-[0.98]",
            selectedId === photo.id ? "ring-2 ring-primary" : null
          )}
          onClick={() => onSelect(photo.id)}
        >
          <CardHeader>
            <CardTitle>Photo {photo.id}</CardTitle>
            <CardAction>
              {selectedId === photo.id ? <Badge>Refining</Badge> : <Badge variant="secondary">Select</Badge>}
            </CardAction>
            <CardDescription>{new Date(photo.created_at).toLocaleString()}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-2">
              <figure className="flex flex-col gap-1">
                <img src={photo.original_url} alt={`Original ${photo.id}`} className="aspect-square rounded-lg object-cover" />
                <figcaption className="text-xs text-muted-foreground">Original</figcaption>
              </figure>
              {photo.generated.map((version, index) => (
                <figure key={`${version.url}-${index}`} className="flex flex-col gap-1">
                  <img src={version.url} alt={version.prompt} className="aspect-square rounded-lg object-cover" />
                  <figcaption className="truncate text-xs text-muted-foreground">{version.prompt}</figcaption>
                </figure>
              ))}
            </div>
          </CardContent>
          <CardFooter>
            <p className="truncate text-xs text-muted-foreground">
              {photo.generated.at(-1)?.prompt ?? "Waiting for first edit"}
            </p>
          </CardFooter>
        </Card>
      ))}
    </div>
  )
}
