"use client"

import { useMemo } from "react"
import DiffMatchPatch from "diff-match-patch"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"

interface DiffViewerProps {
  oldText: string
  newText: string
  fileName?: string
  showLineNumbers?: boolean
}

export function DiffViewer({ oldText, newText, fileName, showLineNumbers = true }: DiffViewerProps) {
  const diffs = useMemo(() => {
    const dmp = new DiffMatchPatch()
    const diff = dmp.diff_main(oldText || "", newText || "")
    dmp.diff_cleanupSemantic(diff)
    return diff
  }, [oldText, newText])

  const renderDiff = () => {
    const lines: JSX.Element[] = []
    let lineNumber = 1
    let currentLine: { type: string; content: string; oldLine?: number; newLine?: number }[] = []

    const flushLine = () => {
      if (currentLine.length > 0) {
        const lineType = currentLine.some((part) => part.type === "added")
          ? "added"
          : currentLine.some((part) => part.type === "removed")
            ? "removed"
            : "unchanged"

        lines.push(
          <div
            key={lineNumber}
            className={`flex font-mono text-sm ${
              lineType === "added"
                ? "bg-green-50 dark:bg-green-950"
                : lineType === "removed"
                  ? "bg-red-50 dark:bg-red-950"
                  : ""
            }`}
          >
            {showLineNumbers && (
              <div className="w-12 flex-shrink-0 text-right pr-4 text-gray-500 select-none border-r border-gray-200 dark:border-gray-700">
                {lineNumber}
              </div>
            )}
            <div className="flex-1 px-4 py-1 whitespace-pre-wrap break-all">
              {currentLine.map((part, idx) => (
                <span
                  key={idx}
                  className={
                    part.type === "added"
                      ? "bg-green-200 dark:bg-green-900"
                      : part.type === "removed"
                        ? "bg-red-200 dark:bg-red-900"
                        : ""
                  }
                >
                  {part.content}
                </span>
              ))}
            </div>
          </div>,
        )
        currentLine = []
        lineNumber++
      }
    }

    diffs.forEach(([type, text]) => {
      const lines = text.split("\n")

      lines.forEach((line, idx) => {
        if (idx > 0) {
          flushLine()
        }

        const diffType = type === 1 ? "added" : type === -1 ? "removed" : "unchanged"

        if (line || idx === 0) {
          currentLine.push({
            type: diffType,
            content: line,
          })
        }
      })
    })

    flushLine()

    return lines
  }

  const stats = useMemo(() => {
    let added = 0
    let removed = 0
    diffs.forEach(([type, text]) => {
      if (type === 1) added += text.length
      if (type === -1) removed += text.length
    })
    return { added, removed }
  }, [diffs])

  return (
    <Card className="overflow-hidden">
      {fileName && (
        <div className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-4 py-3 flex items-center justify-between">
          <div className="font-mono text-sm font-semibold">{fileName}</div>
          <div className="flex gap-2">
            <Badge variant="outline" className="bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-400">
              +{stats.added}
            </Badge>
            <Badge variant="outline" className="bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-400">
              -{stats.removed}
            </Badge>
          </div>
        </div>
      )}
      <ScrollArea className="h-[600px]">
        <div className="min-w-full">{renderDiff()}</div>
      </ScrollArea>
    </Card>
  )
}

interface SideBySideDiffViewerProps {
  oldText: string
  newText: string
  fileName?: string
}

export function SideBySideDiffViewer({ oldText, newText, fileName }: SideBySideDiffViewerProps) {
  const oldLines = (oldText || "").split("\n")
  const newLines = (newText || "").split("\n")
  const maxLines = Math.max(oldLines.length, newLines.length)

  return (
    <Card className="overflow-hidden">
      {fileName && (
        <div className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-4 py-3">
          <div className="font-mono text-sm font-semibold">{fileName}</div>
        </div>
      )}
      <div className="grid grid-cols-2 divide-x divide-gray-200 dark:divide-gray-700">
        <div className="bg-red-50 dark:bg-red-950">
          <div className="bg-red-100 dark:bg-red-900 px-4 py-2 font-semibold text-sm border-b border-red-200 dark:border-red-800">
            Before
          </div>
          <ScrollArea className="h-[600px]">
            {oldLines.map((line, idx) => (
              <div key={idx} className="flex font-mono text-sm">
                <div className="w-12 flex-shrink-0 text-right pr-4 text-gray-500 select-none border-r border-red-200 dark:border-red-800">
                  {idx + 1}
                </div>
                <div className="flex-1 px-4 py-1 whitespace-pre-wrap break-all">{line}</div>
              </div>
            ))}
          </ScrollArea>
        </div>
        <div className="bg-green-50 dark:bg-green-950">
          <div className="bg-green-100 dark:bg-green-900 px-4 py-2 font-semibold text-sm border-b border-green-200 dark:border-green-800">
            After
          </div>
          <ScrollArea className="h-[600px]">
            {newLines.map((line, idx) => (
              <div key={idx} className="flex font-mono text-sm">
                <div className="w-12 flex-shrink-0 text-right pr-4 text-gray-500 select-none border-r border-green-200 dark:border-green-800">
                  {idx + 1}
                </div>
                <div className="flex-1 px-4 py-1 whitespace-pre-wrap break-all">{line}</div>
              </div>
            ))}
          </ScrollArea>
        </div>
      </div>
    </Card>
  )
}
