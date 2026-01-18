import { Link, useLocation, useNavigate } from "react-router-dom";
import { LogOut, User } from "lucide-react";
import { useEffect, useState } from "react";
import { getCurrentUser, logout, type User as UserType } from "../lib/auth";

export function AppNavbar() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const [user, setUser] = useState<UserType | null>(null);

  // Only read user for display — DO NOT redirect here.
  useEffect(() => {
    setUser(getCurrentUser());
  }, []);

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  const navItems = [
    { name: "Dashboard", href: "/dashboard" },
    { name: "Copilot", href: "/copilot" },
    { name: "Docs", href: "/docs" },
  ];

  const isActive = (href: string) => pathname === href;

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-16 items-center justify-between px-6">
        {/* Logo */}
        <Link to="/dashboard" className="flex items-center gap-3">
          <img
            src="/logo.png"
            alt="BNPL Copilot"
            width={56}
            height={56}
            className="h-14 w-14 object-contain"
          />
          <span className="text-lg font-semibold text-[#303848]">
            BNPL Copilot
          </span>
        </Link>

        {/* Centered Navigation */}
        <nav className="flex items-center gap-1 rounded-full bg-[#F8F8F8] p-1">
          {navItems.map((item) => (
            <Link
              key={item.name}
              to={item.href}
              className={`rounded-full px-5 py-2 text-sm font-medium transition-all ${
                isActive(item.href)
                  ? "bg-[#582098] text-white shadow-sm"
                  : "text-[#505050] hover:bg-white hover:text-[#303848]"
              }`}
            >
              {item.name}
            </Link>
          ))}
        </nav>

        {/* User Menu */}
        <div className="flex items-center gap-4">
          {user ? (
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 rounded-full bg-[#F8F8F8] px-3 py-1.5">
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-[#582098]/10">
                  <User className="h-3.5 w-3.5 text-[#582098]" />
                </div>
                <span className="text-sm font-medium text-[#303848]">
                  {user.name}
                </span>
                <span className="rounded-full bg-[#582098]/10 px-2 py-0.5 text-xs font-medium capitalize text-[#582098]">
                  {user.role}
                </span>
              </div>

              <button
                onClick={handleLogout}
                className="flex h-8 w-8 items-center justify-center rounded-full text-[#505050] transition-colors hover:bg-[#F8F8F8] hover:text-[#582098]"
                title="Sign out"
                type="button"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          ) : (
            // Optional: if somehow navbar renders without a user, show a subtle sign-in link
            <button
              type="button"
              onClick={() => navigate("/login")}
              className="text-sm font-medium text-[#505050] hover:text-[#582098] transition-colors"
            >
              Sign in
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
