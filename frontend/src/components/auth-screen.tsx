import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

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
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
  FieldLegend,
  FieldSet,
} from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import { Textarea } from "@/components/ui/textarea"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { login, queryKeys, register, type Profile } from "@/lib/api"

type Mode = "login" | "register"

export function AuthScreen() {
  const queryClient = useQueryClient()
  const [mode, setMode] = useState<Mode>("login")
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [colors, setColors] = useState(["", "", ""])
  const [hobbies, setHobbies] = useState("")
  const [notes, setNotes] = useState("")

  const auth = useMutation({
    mutationFn: async (): Promise<Profile> => {
      if (mode === "login") {
        return login({ username, password })
      }
      const favorite_colors = colors.map((color) => color.trim()).filter(Boolean)
      return register({
        username,
        password,
        favorite_colors,
        hobbies: hobbies.trim(),
        notes: notes.trim(),
      })
    },
    onSuccess: (profile) => {
      queryClient.setQueryData(queryKeys.profile, profile)
      toast.success(mode === "login" ? "Signed in" : "Account ready")
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : "Could not sign in")
    },
  })

  return (
    <div className="flex min-h-[100dvh] items-center justify-center px-4 py-10">
      <div className="grid w-full max-w-5xl items-center gap-10 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="flex max-w-md flex-col gap-4">
          <p className="text-xs tracking-[0.28em] text-primary uppercase">Photogen</p>
          <h1 className="font-heading text-4xl tracking-tight text-balance md:text-5xl">
            A darkroom for the picture you already have.
          </h1>
          <p className="max-w-[42ch] text-muted-foreground">
            Upload a photo, describe the look, and keep both the original and the edit.
          </p>
        </div>

        <Card className="w-full max-w-md justify-self-end">
          <CardHeader>
            <CardTitle>{mode === "login" ? "Sign in" : "Create a studio"}</CardTitle>
            <CardDescription>
              {mode === "login"
                ? "Use the username and password you registered with."
                : "Taste notes help the model match you. The backend never sees preset ids."}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form
              className="flex flex-col gap-5"
              onSubmit={(event) => {
                event.preventDefault()
                auth.mutate()
              }}
            >
              <ToggleGroup
                type="single"
                value={mode}
                onValueChange={(value) => {
                  if (value === "login" || value === "register") {
                    setMode(value)
                  }
                }}
                spacing={2}
                variant="outline"
              >
                <ToggleGroupItem value="login">Sign in</ToggleGroupItem>
                <ToggleGroupItem value="register">Register</ToggleGroupItem>
              </ToggleGroup>

              <FieldGroup>
                <Field>
                  <FieldLabel htmlFor="username">Username</FieldLabel>
                  <Input
                    id="username"
                    autoComplete="username"
                    value={username}
                    onChange={(event) => setUsername(event.target.value)}
                    minLength={mode === "register" ? 3 : 1}
                    maxLength={32}
                    required
                  />
                  {mode === "register" ? (
                    <FieldDescription>Letters and numbers only, 3–32 characters.</FieldDescription>
                  ) : null}
                </Field>
                <Field>
                  <FieldLabel htmlFor="password">Password</FieldLabel>
                  <Input
                    id="password"
                    type="password"
                    autoComplete={mode === "login" ? "current-password" : "new-password"}
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    minLength={mode === "register" ? 6 : 1}
                    required
                  />
                </Field>

                {mode === "register" ? (
                  <>
                    <FieldSet>
                      <FieldLegend variant="label">Favorite colors</FieldLegend>
                      <FieldDescription>Up to three. Used when the model asks for your profile.</FieldDescription>
                      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                        {colors.map((color, index) => (
                          <Field key={index}>
                            <FieldLabel htmlFor={`color-${index}`} className="sr-only">
                              Color {index + 1}
                            </FieldLabel>
                            <Input
                              id={`color-${index}`}
                              placeholder={`Color ${index + 1}`}
                              value={color}
                              onChange={(event) => {
                                const next = [...colors]
                                next[index] = event.target.value
                                setColors(next)
                              }}
                              maxLength={32}
                            />
                          </Field>
                        ))}
                      </div>
                    </FieldSet>
                    <Field>
                      <FieldLabel htmlFor="hobbies">Hobbies</FieldLabel>
                      <Input
                        id="hobbies"
                        value={hobbies}
                        onChange={(event) => setHobbies(event.target.value)}
                        maxLength={200}
                        required
                      />
                    </Field>
                    <Field>
                      <FieldLabel htmlFor="notes">Notes</FieldLabel>
                      <Textarea
                        id="notes"
                        value={notes}
                        onChange={(event) => setNotes(event.target.value)}
                        maxLength={200}
                        rows={3}
                      />
                      <FieldDescription>Optional. Anything the edit should remember.</FieldDescription>
                    </Field>
                  </>
                ) : null}
              </FieldGroup>

              <Button type="submit" disabled={auth.isPending}>
                {auth.isPending ? <Spinner data-icon="inline-start" /> : null}
                {mode === "login" ? "Enter the studio" : "Register"}
              </Button>
            </form>
          </CardContent>
          <CardFooter>
            <p className="text-xs text-muted-foreground">
              Session cookie is HTTP-only. The browser never reads it from JavaScript.
            </p>
          </CardFooter>
        </Card>
      </div>
    </div>
  )
}
