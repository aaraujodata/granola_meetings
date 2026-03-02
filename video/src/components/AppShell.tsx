import { AbsoluteFill } from "remotion";
import { fontFamilySans } from "../lib/fonts";

type AppShellProps = {
  activeNav: "Dashboard" | "Meetings" | "Search" | "Pipeline";
  children: React.ReactNode;
};

const navItems = ["Dashboard", "Meetings", "Search", "Pipeline"] as const;

export const AppShell: React.FC<AppShellProps> = ({ activeNav, children }) => {
  return (
    <AbsoluteFill className="bg-gray-50">
      <div className="flex h-full" style={{ fontFamily: fontFamilySans }}>
        {/* Sidebar */}
        <nav className="w-64 shrink-0 border-r-2 border-gray-200 bg-white">
          <div className="px-5 py-8">
            <h1 className="text-2xl font-bold text-gray-800">Granola</h1>
            <p className="text-sm text-gray-400">Meeting Explorer</p>
          </div>
          <ul className="space-y-1 px-3">
            {navItems.map((item) => (
              <li key={item}>
                <div
                  className={`block rounded-lg px-4 py-3 text-base font-semibold ${
                    item === activeNav
                      ? "bg-blue-50 text-blue-700"
                      : "text-gray-600"
                  }`}
                >
                  {item}
                </div>
              </li>
            ))}
          </ul>
        </nav>

        {/* Main content */}
        <main className="flex-1 overflow-hidden p-10">{children}</main>
      </div>
    </AbsoluteFill>
  );
};
