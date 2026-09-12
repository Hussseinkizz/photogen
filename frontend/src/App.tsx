import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query"

import { AuthScreen } from "@/components/auth-screen"
import { Studio } from "@/components/studio"
import { Skeleton } from "@/components/ui/skeleton"
import { Toaster } from "@/components/ui/sonner"
import { getProfile, queryKeys } from "@/lib/api"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      refetchOnWindowFocus: false,
    },
  },
})

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Toaster theme="dark" />
      <Root />
    </QueryClientProvider>
  )
}

function Root() {
  const profile = useQuery({
    queryKey: queryKeys.profile,
    queryFn: getProfile,
  })

  if (profile.isPending) {
    return (
      <div className="flex min-h-[100dvh] flex-col gap-6 px-6 py-8">
        <Skeleton className="h-10 w-40" />
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Skeleton className="h-80" />
          <Skeleton className="h-80" />
        </div>
      </div>
    )
  }

  if (!profile.data) {
    return <AuthScreen />
  }

  return <Studio profile={profile.data} />
}

export default App
