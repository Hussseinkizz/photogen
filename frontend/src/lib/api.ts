export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

export type Profile = {
  id: number
  username: string
  favorite_colors: string[]
  hobbies: string
  notes: string
}

export type PhotoEdit = {
  url: string
  prompt: string
}

export type Photo = {
  id: number
  original_url: string
  generated: PhotoEdit[]
  parent_id: number | null
  created_at: string
}

export type LoginInput = {
  username: string
  password: string
}

export type RegisterInput = LoginInput & {
  favorite_colors: string[]
  hobbies: string
  notes: string
}

export const queryKeys = {
  profile: ["profile"] as const,
  photos: ["photos"] as const,
}

function readDetail(body: unknown, fallback: string): string {
  if (!body || typeof body !== "object" || !("detail" in body)) {
    return fallback
  }
  const detail = (body as { detail: unknown }).detail
  if (typeof detail === "string") {
    return detail
  }
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") {
          return item
        }
        if (item && typeof item === "object" && "msg" in item) {
          return String((item as { msg: unknown }).msg)
        }
        return ""
      })
      .filter(Boolean)
      .join(". ")
  }
  return fallback
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers)
  if (init?.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json")
  }
  const response = await fetch(path, {
    ...init,
    credentials: "include",
    headers,
  })
  if (!response.ok) {
    let detail = response.statusText
    try {
      detail = readDetail(await response.json(), detail)
    } catch {
      // Keep status text when the body is not JSON.
    }
    throw new ApiError(detail, response.status)
  }
  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

export function getProfile(): Promise<Profile> {
  return request<Profile>("/api/profile")
}

export function login(input: LoginInput): Promise<Profile> {
  return request<Profile>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(input),
  })
}

export function register(input: RegisterInput): Promise<Profile> {
  return request<Profile>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify(input),
  })
}

export function logout(): Promise<{ ok: boolean }> {
  return request<{ ok: boolean }>("/api/auth/logout", { method: "POST" })
}

export function listPhotos(): Promise<Photo[]> {
  return request<Photo[]>("/api/photos")
}

export function createPhoto(input: { prompt: string; image: File }): Promise<Photo> {
  const body = new FormData()
  body.append("prompt", input.prompt)
  body.append("image", input.image)
  return request<Photo>("/api/photos", { method: "POST", body })
}

export function addPhotoVersion(photoId: number, prompt: string): Promise<Photo> {
  const body = new FormData()
  body.append("prompt", prompt)
  return request<Photo>(`/api/photos/${photoId}`, { method: "POST", body })
}

export function latestImageUrl(photo: Photo): string {
  const last = photo.generated.at(-1)
  return last?.url ?? photo.original_url
}
