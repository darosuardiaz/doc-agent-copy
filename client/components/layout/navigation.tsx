"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { FileText, Upload, Brain, MessageSquare, Settings, BookOpen } from "lucide-react"

const navigation = [
  { name: "Documents", href: "/documents", icon: FileText },
  { name: "Upload", href: "/upload", icon: Upload },
  { name: "Research", href: "/research", icon: Brain },
  { name: "Chat", href: "/chat", icon: MessageSquare },
  { name: "System", href: "/system", icon: Settings },
]

export function Navigation() {
  const pathname = usePathname()

  return (
    <header className="border-b bg-background">
      <div className="flex h-16 items-center px-6">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <BookOpen className="h-6 w-6 text-blue-600" />
          <span className="text-lg">Financial Document AI</span>
        </Link>

        <nav className="ml-auto flex items-center gap-1">
          {navigation.map((item) => {
            const Icon = item.icon
            const isActive = pathname.startsWith(item.href)

            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-md transition-colors",
                  isActive
                    ? "bg-blue-100 text-blue-700" // reverted back to previous blue colors
                    : "text-muted-foreground hover:text-foreground hover:bg-muted",
                )}
              >
                <Icon className="h-4 w-4" />
                {item.name}
              </Link>
            )
          })}
        </nav>
      </div>
    </header>
  )
}
