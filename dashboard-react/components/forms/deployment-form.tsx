"use client"

import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { apiClient } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Loader2 } from "lucide-react"
import { toast } from "sonner"

const deploymentSchema = z.object({
  name: z.string().min(1, "Name is required"),
  server_id: z.string().min(1, "Server is required"),
  path: z.string().min(1, "Path is required"),
  config_path: z.string().optional(),
})

type DeploymentFormValues = z.infer<typeof deploymentSchema>

interface DeploymentFormProps {
  deployment?: any
  onSuccess: () => void
}

export function DeploymentForm({ deployment, onSuccess }: DeploymentFormProps) {
  const queryClient = useQueryClient()

  const { data: servers } = useQuery({
    queryKey: ["servers"],
    queryFn: async () => {
      const response = await apiClient.get("/servers")
      return response.data
    },
  })

  const form = useForm<DeploymentFormValues>({
    resolver: zodResolver(deploymentSchema),
    defaultValues: {
      name: "",
      server_id: "",
      path: "",
      config_path: "",
    },
  })

  useEffect(() => {
    if (deployment) {
      form.reset({
        name: deployment.name,
        server_id: deployment.server_id,
        path: deployment.path,
        config_path: deployment.config_path || "",
      })
    }
  }, [deployment, form])

  const mutation = useMutation({
    mutationFn: async (data: DeploymentFormValues) => {
      // Convert server_id string to number for the array of target_servers
      const serverId = parseInt(data.server_id, 10);
      
      const payload = {
        name: data.name,
        target_servers: [serverId],
        deploy_all: false,
        skip_validation: false,
        skip_backup: false,
        auto_restart: true,
        // The path and config_path are not in the DeploymentCreate schema directly
        // They should probably be in metadata or passed if the schema supports it.
        // Looking at DeploymentCreate in backend:
        // commit_sha, commit_message, branch, trigger, metadata
        // It seems 'path' is not a standard field. 
        // We will put extra fields in metadata for now if they are needed, 
        // or just ignore them if the backend logic handles deployment paths differently.
        metadata: {
           path: data.path,
           config_path: data.config_path
        }
      };

      if (deployment) {
        await apiClient.put(`/deployments/${deployment.id}`, payload)
      } else {
        await apiClient.post("/deployments", payload)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["deployments"] })
      toast.success(deployment ? "Deployment updated successfully" : "Deployment created successfully")
      onSuccess()
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Operation failed")
    },
  })

  const onSubmit = (data: DeploymentFormValues) => {
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
              <FormLabel>Deployment Name</FormLabel>
              <FormControl>
                <Input placeholder="Home Assistant Production" {...field} />
              </FormControl>
              <FormDescription>A friendly name for this deployment</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="server_id"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Server</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a server" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {servers?.map((server: any) => (
                    <SelectItem key={server.id} value={server.id}>
                      {server.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormDescription>The server where HA is deployed</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="path"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Installation Path</FormLabel>
              <FormControl>
                <Input placeholder="/opt/homeassistant" {...field} />
              </FormControl>
              <FormDescription>Path to HA installation directory</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="config_path"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Config Path (Optional)</FormLabel>
              <FormControl>
                <Input placeholder="/config" {...field} />
              </FormControl>
              <FormDescription>Path to HA configuration directory</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="flex justify-end gap-2">
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {deployment ? "Update Deployment" : "Create Deployment"}
          </Button>
        </div>
      </form>
    </Form>
  )
}
