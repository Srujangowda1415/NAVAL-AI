"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Radar, LayoutDashboard, Upload, History, FileText, Settings, Info } from "lucide-react";
import clsx from "clsx";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/upload", label: "Upload", icon: Upload },
  { href: "/history", label: "History", icon: History },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/settings", label: "Settings", icon: Settings },
  { href: "/about", label: "About", icon: Info },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 border-b border-navy-border bg-abyss/90 backdrop-blur">
      <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <Link href="/" className="flex items-center gap-2.5 font-display text-lg font-semibold tracking-wide">
          <Radar size={22} className="text-steel-bright" aria-hidden />
          NAVAL&nbsp;AI
        </Link>

        <div className="hidden items-center gap-1 md:flex">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
            const active = pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={clsx(
                  "flex items-center gap-1.5 rounded-sm px-3 py-2 font-data text-xs tracking-wide transition-colors",
                  active ? "bg-navy-light text-steel-bright" : "text-mist hover:bg-navy-light hover:text-white",
                )}
              >
                <Icon size={14} aria-hidden />
                {label.toUpperCase()}
              </Link>
            );
          })}
        </div>
      </nav>
    </header>
  );
}
