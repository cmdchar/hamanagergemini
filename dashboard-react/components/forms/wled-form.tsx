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

const wledSchema = z.object({
  name: z.string().min(1, "Name is required"),
  host: z.string().min(1, "Host is required"),
  port: z.coerce.number().min(1).max(65535, "Port must be between 1 and 65535"),
})

type WLEDFormValues = z.infer<typeof wledSchema>

interface WLEDFormProps {
  device?: any
  onSuccess: () => void
}

export function WLEDForm({ device, onSuccess }: WLEDFormProps) {
  const queryClient = useQueryClient()

  const form = useForm<WLEDFormValues>({
    resolver: zodResolver(wledSchema),
    defaultValues: {
      name: "",
      host: "",
      port: 80,
    },
  })

  useEffect(() => {
    if (device) {
      form.reset({
        name: device.name,
        host: device.host,
        port: device.port,
      })
    }
  }, [device, form])

  const mutation = useMutation({
    mutationFn: async (data: WLEDFormValues) => {
      if (device) {
        await apiClient.put(`/wled/${device.id}`, data)
      } else {
        await apiClient.post("/wled", data)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wled-devices"] })
      toast.success(device ? "Device updated successfully" : "Device added successfully")
      onSuccess()
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Operation failed")
    },
  })

  const onSubmit = (data: WLEDFormValues) => {
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
              <FormLabel>Device Name</FormLabel>
              <FormControl>
                <Input placeholder="Living Room LEDs" {...field} />
              </FormControl>
              <FormDescription>A friendly name for this device</FormDescription>
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
                <Input placeholder="192.168.1.50" {...field} />
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
                <Input type="number" placeholder="80" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="flex justify-end gap-2">
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {device ? "Update Device" : "Add Device"}
          </Button>
        </div>
      </form>
    </Form>
  )
}
