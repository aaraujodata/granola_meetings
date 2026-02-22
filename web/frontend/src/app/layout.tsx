import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Granola Meetings",
  description: "Browse, search, and manage Granola meeting exports",
};

const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/meetings", label: "Meetings" },
  { href: "/search", label: "Search" },
  { href: "/pipeline", label: "Pipeline" },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 antialiased">
        <div className="flex min-h-screen">
          {/* Sidebar */}
          <nav className="w-56 shrink-0 border-r border-gray-200 bg-white">
            <div className="px-4 py-6">
              <h1 className="text-lg font-bold text-gray-800">
                Granola
              </h1>
              <p className="text-xs text-gray-400">Meeting Explorer</p>
            </div>
            <ul className="space-y-1 px-2">
              {navItems.map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className="block rounded-md px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                  >
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          {/* Main content */}
          <main className="flex-1 overflow-auto p-8">{children}</main>
        </div>
      </body>
    </html>
  );
}
