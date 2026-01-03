"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import {
    Home,
    Calendar,
    TrendingUp,
    BarChart3,
    Users,
    Settings,
    Zap,
    Trophy
} from "lucide-react"

const navigation = [
    { name: "Dashboard", href: "/", icon: Home },
    { name: "Matches", href: "/matches", icon: Calendar },
    { name: "Predictions", href: "/predictions", icon: TrendingUp },
    { name: "Value Bets", href: "/value-bets", icon: Zap },
    { name: "Analytics", href: "/analytics", icon: BarChart3 },
    { name: "Teams", href: "/teams", icon: Users },
    { name: "Settings", href: "/settings", icon: Settings },
]

export function Sidebar() {
    const pathname = usePathname()

    return (
        <aside className="fixed inset-y-0 left-0 z-50 w-64 border-r bg-card">
            {/* Logo */}
            <div className="flex h-16 items-center gap-2 border-b px-6">
                <Trophy className="h-8 w-8 text-primary" />
                <div>
                    <h1 className="font-bold text-lg">Football Predictor</h1>
                    <p className="text-xs text-muted-foreground">Pro Edition</p>
                </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 space-y-1 p-4">
                {navigation.map((item) => {
                    const isActive = pathname === item.href
                    return (
                        <Link
                            key={item.name}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                                isActive
                                    ? "bg-primary text-primary-foreground"
                                    : "text-muted-foreground hover:bg-accent hover:text-foreground"
                            )}
                        >
                            <item.icon className="h-5 w-5" />
                            {item.name}
                        </Link>
                    )
                })}
            </nav>

            {/* User section */}
            <div className="border-t p-4">
                <div className="flex items-center gap-3 rounded-lg bg-muted/50 p-3">
                    <div className="h-9 w-9 rounded-full bg-primary/20 flex items-center justify-center">
                        <span className="text-sm font-medium text-primary">FP</span>
                    </div>
                    <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">Free Plan</p>
                        <p className="text-xs text-muted-foreground">Upgrade to Pro</p>
                    </div>
                </div>
            </div>
        </aside>
    )
}
