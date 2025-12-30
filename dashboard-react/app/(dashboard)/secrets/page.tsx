"use client"

import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiClient } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  ResponsiveTable,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/responsive-table"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Plus, Trash2, AlertCircle, Loader2, Eye, EyeOff, Copy, Lock } from "lucide-react"
import { toast } from "sonner"
import { SecretForm } from "@/components/forms/secret-form"

interface Secret {
  id: string
  key: string
  description: string
  encrypted: boolean
  created_at: string
  updated_at: string
}

export default function SecretsPage() {
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingSecret, setEditingSecret] = useState<Secret | null>(null)
  const [decryptedValues, setDecryptedValues] = useState<Record<string, string>>({})
  const queryClient = useQueryClient()

  const {
    data: secrets,
    isLoading,
    error,
  } = useQuery<Secret[]>({
    queryKey: ["secrets"],
    queryFn: async () => {
      const response = await apiClient.get("/security/secrets")
      return response.data
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/security/secrets/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["secrets"] })
      toast.success("Secret deleted successfully")
    },
    onError: () => {
      toast.error("Failed to delete secret")
    },
  })

  const decryptMutation = useMutation({
    mutationFn: async (id: string) => {
      const response = await apiClient.post(`/security/secrets/${id}/decrypt`)
      return { id, value: response.data.value }
    },
    onSuccess: ({ id, value }) => {
      setDecryptedValues((prev) => ({ ...prev, [id]: value }))
      toast.success("Secret decrypted")
    },
    onError: () => {
      toast.error("Failed to decrypt secret")
    },
  })

  const handleEdit = (secret: Secret) => {
    setEditingSecret(secret)
    setDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
    setEditingSecret(null)
  }

  const toggleDecrypt = (secretId: string) => {
    if (decryptedValues[secretId]) {
      setDecryptedValues((prev) => {
        const newValues = { ...prev }
        delete newValues[secretId]
        return newValues
      })
    } else {
      decryptMutation.mutate(secretId)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast.success("Copied to clipboard")
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Secrets Management</h1>
            <p className="text-muted-foreground">Manage encrypted secrets with AES-256-GCM</p>
          </div>
          <Skeleton className="h-10 w-32" />
        </div>
        <Card>
          <CardContent className="p-6">
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Secrets Management</h1>
          <p className="text-muted-foreground">Manage encrypted secrets with AES-256-GCM</p>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>Failed to load secrets. Please try again.</AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Secrets Management</h1>
          <p className="text-muted-foreground">Manage encrypted secrets with AES-256-GCM</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={() => setEditingSecret(null)}>
              <Plus className="mr-2 h-4 w-4" />
              Add Secret
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{editingSecret ? "Edit Secret" : "Add New Secret"}</DialogTitle>
              <DialogDescription>
                {editingSecret ? "Update the secret configuration" : "Create a new encrypted secret"}
              </DialogDescription>
            </DialogHeader>
            <SecretForm secret={editingSecret} onSuccess={handleCloseDialog} />
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Lock className="h-5 w-5" />
            <CardTitle>Encrypted Secrets</CardTitle>
          </div>
          <CardDescription>AES-256-GCM encrypted key-value pairs</CardDescription>
        </CardHeader>
        <CardContent>
          {secrets && secrets.length > 0 ? (
            <ResponsiveTable>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Key</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Value</TableHead>
                    <TableHead>Encryption</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {secrets.map((secret) => (
                    <TableRow key={secret.id}>
                      <TableCell className="font-medium">{secret.key}</TableCell>
                      <TableCell className="text-muted-foreground">{secret.description}</TableCell>
                      <TableCell>
                        {decryptedValues[secret.id] ? (
                          <div className="flex items-center gap-2">
                            <code className="text-sm bg-muted px-2 py-1 rounded">{decryptedValues[secret.id]}</code>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => copyToClipboard(decryptedValues[secret.id])}
                            >
                              <Copy className="h-3 w-3" />
                            </Button>
                          </div>
                        ) : (
                          <span className="text-muted-foreground">••••••••</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant={secret.encrypted ? "default" : "secondary"}>
                          {secret.encrypted ? "AES-256-GCM" : "Plain"}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => toggleDecrypt(secret.id)}
                            disabled={decryptMutation.isPending}
                          >
                            {decryptMutation.isPending ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : decryptedValues[secret.id] ? (
                              <EyeOff className="h-4 w-4" />
                            ) : (
                              <Eye className="h-4 w-4" />
                            )}
                          </Button>
                          <Button variant="outline" size="sm" onClick={() => handleEdit(secret)}>
                            Edit
                          </Button>
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => deleteMutation.mutate(secret.id)}
                            disabled={deleteMutation.isPending}
                          >
                            {deleteMutation.isPending ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Trash2 className="h-4 w-4" />
                            )}
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </ResponsiveTable>
          ) : (
            <div className="text-center py-12">
              <p className="text-muted-foreground">No secrets configured yet</p>
              <Button className="mt-4" onClick={() => setDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Add Your First Secret
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
