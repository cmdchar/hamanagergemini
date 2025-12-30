import type * as React from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { cn } from "@/lib/utils"

interface ResponsiveTableProps {
  children: React.ReactNode
  className?: string
}

export function ResponsiveTable({ children, className }: ResponsiveTableProps) {
  return (
    <div className="w-full overflow-auto">
      <div className={cn("min-w-[640px]", className)}>{children}</div>
    </div>
  )
}

export function ResponsiveTableWrapper({ children, className }: ResponsiveTableProps) {
  return (
    <div className={cn("rounded-md border", className)}>
      <ResponsiveTable>{children}</ResponsiveTable>
    </div>
  )
}

export { Table, TableBody, TableCell, TableHead, TableHeader, TableRow }
