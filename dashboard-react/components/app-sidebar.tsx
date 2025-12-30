"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  Home,
  Server,
  Rocket,
  Lightbulb,
  Radio,
  Network,
  Cpu,
  Database,
  Bot,
  Lock,
  FileText,
  LogOut,
  Terminal,
} from "lucide-react"
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarFooter,
} from "@/components/ui/sidebar"
import { useAuthStore } from "@/store/auth-store"
import { Button } from "@/components/ui/button"
import { useRouter } from "next/navigation"

const navItems = [
  { title: "Dashboard", icon: Home, href: "/dashboard" },
  { title: "Servers", icon: Server, href: "/servers" },
  { title: "Deployments", icon: Rocket, href: "/deployments" },
  { title: "WLED", icon: Lightbulb, href: "/wled" },
  { title: "FPP", icon: Radio, href: "/fpp" },
  { title: "Tailscale", icon: Network, href: "/tailscale" },
  { title: "ESPHome", icon: Cpu, href: "/esphome" },
  { title: "Backups", icon: Database, href: "/backups" },
  { title: "AI Assistant", icon: Bot, href: "/ai-assistant" },
  { title: "Secrets", icon: Lock, href: "/secrets" },
  { title: "Audit Logs", icon: FileText, href: "/audit-logs" },
]

export function AppSidebar() {
  const pathname = usePathname()
  const router = useRouter()
  const { logout, user } = useAuthStore()

  const handleLogout = () => {
    logout()
    router.push("/login")
  }

  return (
    <Sidebar>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>HA Config Manager</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.href}>
                  <SidebarMenuButton asChild isActive={pathname === item.href}>
                    <Link href={item.href}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <div className="p-4 border-t">
          <div className="flex items-center justify-between">
            <div className="text-sm">
              <p className="font-medium">{user?.username}</p>
              <p className="text-xs text-muted-foreground">{user?.email}</p>
            </div>
            <Button variant="ghost" size="icon" onClick={handleLogout}>
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}
