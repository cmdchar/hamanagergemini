"use client"

import { useEffect, useRef, useState } from "react"
import { Terminal } from "xterm"
import { FitAddon } from "xterm-addon-fit"
import "xterm/css/xterm.css"
import { useAuthStore } from "@/store/auth-store"

interface WebTerminalProps {
  serverId: string
}

export function WebTerminal({ serverId }: WebTerminalProps) {
  const terminalRef = useRef<HTMLDivElement>(null)
  const [terminal, setTerminal] = useState<Terminal | null>(null)
  const { token } = useAuthStore()
  const fitAddonRef = useRef<FitAddon | null>(null)

  useEffect(() => {
    if (!terminalRef.current || !serverId || !token) return

    // Initialize Terminal
    const term = new Terminal({
      cursorBlink: true,
      theme: {
        background: "#09090b", // zinc-950
        foreground: "#f0f0f0",
        cursor: "#ffffff",
      },
      fontFamily: "Menlo, Monaco, 'Courier New', monospace",
      fontSize: 14,
      rows: 24,
      cols: 80,
    })

    const fitAddon = new FitAddon()
    fitAddonRef.current = fitAddon
    term.loadAddon(fitAddon)

    term.open(terminalRef.current)
    fitAddon.fit()

    term.writeln("\x1b[33mConnecting to server...\x1b[0m")

    // WebSocket connection
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8081/api/v1"
    const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws"
    const wsHost = apiUrl.replace(/^http(s)?:\/\//, "")
    const wsUrl = `${wsProtocol}://${wsHost}/terminal/${serverId}?token=${token}`
    
    console.log("Connecting to WS:", wsUrl)
    
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      term.writeln("\x1b[32m*** Connected ***\x1b[0m\r\n")
      fitAddon.fit()
    }

    ws.onmessage = (event) => {
      term.write(event.data)
    }

    ws.onclose = (event) => {
      term.writeln(`\r\n\x1b[31m*** Connection Closed (Code: ${event.code}) ***\x1b[0m\r\n`)
    }

    ws.onerror = (error) => {
      console.error("WebSocket error:", error)
      term.writeln("\r\n\x1b[31m*** Connection Error ***\x1b[0m\r\n")
    }

    term.onData((data) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(data)
      }
    })

    // Handle resize
    const handleResize = () => {
        fitAddon.fit()
    }
    window.addEventListener('resize', handleResize)

    setTerminal(term)

    return () => {
      ws.close()
      term.dispose()
      window.removeEventListener('resize', handleResize)
    }
  }, [serverId, token])

  return <div ref={terminalRef} className="w-full h-[600px] rounded-lg overflow-hidden border bg-zinc-950" />
}
