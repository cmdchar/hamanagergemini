"use client"

import { useEffect, useState } from "react"
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
  port: z.coerce.number().min(1).max(65535, "HA Port must be between 1 and 65535").default(8123),
  access_token: z.string().optional(),
  ha_username: z.string().optional(),
  ha_password: z.string().optional(),
  ssh_host: z.string().optional(),
  ssh_port: z.coerce.number().min(1).max(65535, "SSH Port must be between 1 and 65535").default(22),
  ssh_user: z.string().min(1, "SSH Username is required"),
  ssh_password: z.string().optional(),
  ssh_key_path: z.string().optional(),
  ssh_key_passphrase: z.string().optional(),
  server_type: z.enum(["production", "staging", "development", "test"]).default("production"),
})

type ServerFormValues = z.infer<typeof serverSchema>

interface ServerFormProps {
  server?: any
  onSuccess: () => void
}

export function ServerForm({ server, onSuccess }: ServerFormProps) {
  const queryClient = useQueryClient()
  const [keyFile, setKeyFile] = useState<File | null>(null)

  const form = useForm<ServerFormValues>({
    resolver: zodResolver(serverSchema),
    defaultValues: {
      name: "",
      host: "",
      port: 8123,
      access_token: "",
      ha_username: "",
      ha_password: "",
      ssh_host: "",
      ssh_port: 22,
      ssh_user: "",
      ssh_password: "",
      ssh_key_path: "",
      ssh_key_passphrase: "",
      server_type: "production",
    },
  })

  useEffect(() => {
    if (server) {
      form.reset({
        name: server.name,
        host: server.host,
        port: server.port || 8123,
        access_token: "",
        ha_username: server.ha_username || "",
        ha_password: "",
        ssh_host: server.ssh_host || "",
        ssh_port: server.ssh_port || 22,
        ssh_user: server.ssh_user || "",
        ssh_password: "",
        ssh_key_path: server.ssh_key_path || "",
        ssh_key_passphrase: "",
        server_type: server.server_type || "production",
      })
    }
  }, [server, form])

  const mutation = useMutation({
    mutationFn: async (data: ServerFormValues) => {
      let serverId: number
      let response
      
      if (server) {
        response = await apiClient.put(`/servers/${server.id}`, data)
        serverId = server.id
      } else {
        response = await apiClient.post("/servers", data)
        serverId = response.data.id
      }
      
      if (keyFile) {
        const formData = new FormData()
        formData.append("file", keyFile)
        await apiClient.post(`/servers/${serverId}/upload-key`, formData, {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        })
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
              <FormLabel>Home Assistant Port</FormLabel>
              <FormControl>
                <Input type="number" placeholder="8123" {...field} />
              </FormControl>
              <FormDescription>Home Assistant web interface port</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="access_token"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Home Assistant Access Token</FormLabel>
              <FormControl>
                <Input type="password" placeholder={server ? "Leave blank to keep current" : "Long-lived access token"} {...field} />
              </FormControl>
              <FormDescription>Long-lived access token from Home Assistant</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="ha_username"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Home Assistant Username (optional)</FormLabel>
              <FormControl>
                <Input placeholder="niku" {...field} />
              </FormControl>
              <FormDescription>Username for HA authentication (e.g., niku)</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="ha_password"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Home Assistant Password (optional)</FormLabel>
              <FormControl>
                <Input type="password" placeholder={server ? "Leave blank to keep current" : "HA Password"} {...field} />
              </FormControl>
              <FormDescription>{server && "Leave blank to keep the current password"} Password for HA user login</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="pt-4 border-t">
          <h3 className="text-sm font-semibold mb-3">SSH Connection Settings</h3>

          <FormField
            control={form.control}
            name="ssh_host"
            render={({ field }) => (
              <FormItem>
                <FormLabel>SSH Host (optional)</FormLabel>
                <FormControl>
                  <Input placeholder="Leave blank to use same as host" {...field} />
                </FormControl>
                <FormDescription>Only if different from main host</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="ssh_port"
            render={({ field }) => (
              <FormItem>
                <FormLabel>SSH Port</FormLabel>
                <FormControl>
                  <Input type="number" placeholder="22" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="ssh_user"
            render={({ field }) => (
              <FormItem>
                <FormLabel>SSH Username</FormLabel>
                <FormControl>
                  <Input placeholder="root" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="ssh_password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>SSH Password</FormLabel>
                <FormControl>
                  <Input type="password" placeholder={server ? "Leave blank to keep current" : "Password"} {...field} />
                </FormControl>
                <FormDescription>{server && "Leave blank to keep the current password"}</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="ssh_key_path"
            render={({ field }) => (
              <FormItem>
                <FormLabel>SSH Key Path (server-side)</FormLabel>
                <FormControl>
                  <Input placeholder="/path/to/ssh/key" {...field} />
                </FormControl>
                <FormDescription>Path to key already on server</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormItem>
            <FormLabel>Upload SSH Key</FormLabel>
            <FormControl>
              <Input
                type="file"
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  if (file) {
                    setKeyFile(file)
                  }
                }}
              />
            </FormControl>
            <FormDescription>Upload a new private key file</FormDescription>
            <FormMessage />
          </FormItem>

          <FormField
            control={form.control}
            name="ssh_key_passphrase"
            render={({ field }) => (
              <FormItem>
                <FormLabel>SSH Key Passphrase</FormLabel>
                <FormControl>
                  <Input type="password" placeholder="Passphrase for the key" {...field} />
                </FormControl>
                <FormDescription>If the key is encrypted</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

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
