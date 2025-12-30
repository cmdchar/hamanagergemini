"use client"

import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { apiClient } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Loader2 } from "lucide-react"
import { toast } from "sonner"

const serverSchema = z.object({
  name: z.string().min(1, "Name is required"),
  host: z.string().min(1, "Host is required"),
  port: z.coerce.number().min(1).max(65535, "Port must be between 1 and 65535"),
  username: z.string().min(1, "Username is required"),
  password: z.string().optional(),
})

type ServerFormValues = z.infer<typeof serverSchema>

interface ServerFormProps {
  server?: any
  onSuccess: () => void
}

export function ServerForm({ server, onSuccess }: ServerFormProps) {
  const queryClient = useQueryClient()

  const form = useForm<ServerFormValues>({
    resolver: zodResolver(serverSchema),
    defaultValues: {
      name: "",
      host: "",
      port: 22,
      username: "",
      password: "",
    },
  })

  useEffect(() => {
    if (server) {
      form.reset({
        name: server.name,
        host: server.host,
        port: server.port,
        username: server.username,
        password: "",
      })
    }
  }, [server, form])

  const mutation = useMutation({
    mutationFn: async (data: ServerFormValues) => {
      if (server) {
        await apiClient.put(`/servers/${server.id}`, data)
      } else {
        await apiClient.post("/servers", data)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["servers"] })
      toast.success(server ? "Server updated successfully" : "Server created successfully")
      onSuccess()
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Operation failed")
    },
  })

  const onSubmit = (data: ServerFormValues) => {
    mutation.mutate(data)
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Server Name</FormLabel>
              <FormControl>
                <Input placeholder="My Server" {...field} />
              </FormControl>
              <FormDescription>A friendly name for this server</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="host"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Host</FormLabel>
              <FormControl>
                <Input placeholder="192.168.1.100" {...field} />
              </FormControl>
              <FormDescription>IP address or hostname</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="port"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Port</FormLabel>
              <FormControl>
                <Input type="number" placeholder="22" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="username"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Username</FormLabel>
              <FormControl>
                <Input placeholder="root" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="password"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Password</FormLabel>
              <FormControl>
                <Input type="password" placeholder={server ? "Leave blank to keep current" : "Password"} {...field} />
              </FormControl>
              <FormDescription>{server && "Leave blank to keep the current password"}</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="flex justify-end gap-2">
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {server ? "Update Server" : "Create Server"}
          </Button>
        </div>
      </form>
    </Form>
  )
}
