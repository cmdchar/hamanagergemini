"use client"

import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { apiClient } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Loader2 } from "lucide-react"
import { toast } from "sonner"

const secretSchema = z.object({
  key: z.string().min(1, "Key is required"),
  value: z.string().min(1, "Value is required"),
  description: z.string().optional(),
  encrypted: z.boolean().default(true),
})

type SecretFormValues = z.infer<typeof secretSchema>

interface SecretFormProps {
  secret?: any
  onSuccess: () => void
}

export function SecretForm({ secret, onSuccess }: SecretFormProps) {
  const queryClient = useQueryClient()

  const form = useForm<SecretFormValues>({
    resolver: zodResolver(secretSchema),
    defaultValues: {
      key: "",
      value: "",
      description: "",
      encrypted: true,
    },
  })

  useEffect(() => {
    if (secret) {
      form.reset({
        key: secret.key,
        value: "",
        description: secret.description || "",
        encrypted: secret.encrypted,
      })
    }
  }, [secret, form])

  const mutation = useMutation({
    mutationFn: async (data: SecretFormValues) => {
      if (secret) {
        await apiClient.put(`/security/secrets/${secret.id}`, data)
      } else {
        await apiClient.post("/security/secrets", data)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["secrets"] })
      toast.success(secret ? "Secret updated successfully" : "Secret created successfully")
      onSuccess()
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Operation failed")
    },
  })

  const onSubmit = (data: SecretFormValues) => {
    mutation.mutate(data)
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="key"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Key</FormLabel>
              <FormControl>
                <Input placeholder="DATABASE_PASSWORD" {...field} />
              </FormControl>
              <FormDescription>Unique identifier for the secret</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="value"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Value</FormLabel>
              <FormControl>
                <Textarea placeholder="Enter secret value" {...field} />
              </FormControl>
              <FormDescription>{secret && "Leave blank to keep the current value"}</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Description (Optional)</FormLabel>
              <FormControl>
                <Input placeholder="Database password for production" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="encrypted"
          render={({ field }) => (
            <FormItem className="flex items-center justify-between rounded-lg border p-4">
              <div className="space-y-0.5">
                <FormLabel className="text-base">Encrypt with AES-256-GCM</FormLabel>
                <FormDescription>Store this secret encrypted in the database</FormDescription>
              </div>
              <FormControl>
                <Switch checked={field.value} onCheckedChange={field.onChange} />
              </FormControl>
            </FormItem>
          )}
        />

        <div className="flex justify-end gap-2">
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {secret ? "Update Secret" : "Create Secret"}
          </Button>
        </div>
      </form>
    </Form>
  )
}
