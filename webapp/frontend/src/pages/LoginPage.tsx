import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Mail,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  AlertCircle,
  Shield,
  User,
  BarChart3,
} from "lucide-react";
import {
  authenticateUser,
  users,
  setCurrentUser,
  type UserRole,
} from "../lib/auth";
import { Code } from "lucide-react";

const roleColors: Record<UserRole, string> = {
  admin: "#582098",
  analyst: "#608818",
  viewer: "#505050",
  developer: "#0ea5e9",
};

const roleDescriptions: Record<UserRole, string> = {
  admin: "Full access to all features and settings",
  analyst: "View and export data, create reports",
  viewer: "Read-only access to dashboards",
  developer: "Access to Feedback Dashboard only",
};

const roleIcons: Record<UserRole, typeof Shield> = {
  admin: Shield,
  analyst: BarChart3,
  viewer: User,
  developer: Code,
};

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    // Simulate network delay
    await new Promise((resolve) => setTimeout(resolve, 800));

    const user = authenticateUser(email, password);

    if (user) {
      // Store user in sessionStorage for demo purposes
      setCurrentUser(user);
      // Redirect developers to feedback page only
      if (user.role === "developer") {
        navigate("/feedback", { replace: true });
      } else {
        navigate("/dashboard", { replace: true });
      }
    } else {
      setError("Invalid email or password. Please try again.");
    }

    setIsLoading(false);
  };

  const handleQuickLogin = (userEmail: string, userPassword: string) => {
    setEmail(userEmail);
    setPassword(userPassword);
  };

  return (
    <div className="min-h-screen bg-white flex">
      {/* Left side - Form */}
      <div className="flex-1 flex flex-col justify-center px-4 sm:px-6 lg:px-8 xl:px-12">
        <div className="w-full max-w-md mx-auto">
          {/* Logo */}
          <Link
            to="/"
            className="inline-flex items-center gap-3 text-xl font-semibold text-[#303848] hover:text-[#582098] transition-colors mb-8"
          >
            <img
              src="/logo.png"
              alt="BNPL Copilot"
              width={64}
              height={64}
              className="h-16 w-16 object-contain"
            />
            <span>Intelligent BNPL Copilot</span>
          </Link>

          {/* Header */}
          <div className="mb-8">
            <h1 className="text-2xl sm:text-3xl font-bold text-[#303848] mb-2">
              Welcome back
            </h1>
            <p className="text-[#505050]">
              Sign in to access your BNPL analytics dashboard
            </p>
          </div>

          {/* Error message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email field */}
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-[#303848] mb-2"
              >
                Email address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Mail className="w-5 h-5 text-[#505050]/50" />
                </div>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email"
                  className="w-full pl-12 pr-4 py-3 bg-[#F8F8F8] border border-[#505050]/10 rounded-lg text-[#303848] placeholder-[#505050]/50 focus:outline-none focus:ring-2 focus:ring-[#582098]/20 focus:border-[#582098] transition-all"
                  required
                />
              </div>
            </div>

            {/* Password field */}
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-[#303848] mb-2"
              >
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Lock className="w-5 h-5 text-[#505050]/50" />
                </div>
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full pl-12 pr-12 py-3 bg-[#F8F8F8] border border-[#505050]/10 rounded-lg text-[#303848] placeholder-[#505050]/50 focus:outline-none focus:ring-2 focus:ring-[#582098]/20 focus:border-[#582098] transition-all"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-4 flex items-center text-[#505050]/50 hover:text-[#582098] transition-colors"
                >
                  {showPassword ? (
                    <EyeOff className="w-5 h-5" />
                  ) : (
                    <Eye className="w-5 h-5" />
                  )}
                </button>
              </div>
            </div>

            {/* Submit button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-2 px-6 py-3.5 bg-[#582098] text-white font-medium rounded-lg hover:bg-[#582098]/90 focus:outline-none focus:ring-2 focus:ring-[#582098]/50 focus:ring-offset-2 transition-all disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  <span>Signing in...</span>
                </>
              ) : (
                <>
                  <span>Sign in</span>
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="relative my-8">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-[#505050]/10" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-4 bg-white text-[#505050]">
                Quick login for demo
              </span>
            </div>
          </div>

          {/* Demo account cards */}
          <div className="space-y-3">
            {users.map((u) => {
              const Icon = roleIcons[u.role];
              return (
                <button
                  key={u.id}
                  type="button"
                  onClick={() => handleQuickLogin(u.email, u.password)}
                  className="w-full flex items-center gap-4 p-4 bg-[#F8F8F8] border border-[#505050]/10 rounded-lg hover:border-[#582098]/30 hover:bg-[#F8F8F8]/80 transition-all group text-left"
                >
                  <div
                    className="w-10 h-10 rounded-full flex items-center justify-center"
                    style={{ backgroundColor: `${roleColors[u.role]}15` }}
                  >
                    <Icon className="w-5 h-5" style={{ color: roleColors[u.role] }} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-[#303848] truncate">
                        {u.name}
                      </p>
                      <span
                        className="px-2 py-0.5 text-xs font-medium rounded-full capitalize"
                        style={{
                          backgroundColor: `${roleColors[u.role]}15`,
                          color: roleColors[u.role],
                        }}
                      >
                        {u.role}
                      </span>
                    </div>
                    <p className="text-sm text-[#505050] truncate">
                      {roleDescriptions[u.role]}
                    </p>
                  </div>
                  <ArrowRight className="w-5 h-5 text-[#505050]/30 group-hover:text-[#582098] group-hover:translate-x-1 transition-all" />
                </button>
              );
            })}
          </div>

          {/* Footer link */}
          <p className="mt-8 text-center text-sm text-[#505050]">
            {"Don't have an account? "}
            <Link
              to="/request-access"
              className="font-medium text-[#582098] hover:text-[#582098]/80 transition-colors"
            >
              Request access
            </Link>
          </p>
        </div>
      </div>

      {/* Right side - Visual */}
      <div className="hidden lg:flex flex-1 bg-gradient-to-br from-[#582098] via-[#582098] to-[#B880B8] relative overflow-hidden">
        {/* Background pattern */}
        <div
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fillRule='evenodd'%3E%3Cg fill='%23ffffff' fillOpacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
          }}
        />

        {/* Floating shapes */}
        <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-white/10 rounded-full blur-3xl animate-float" />
        <div
          className="absolute bottom-1/4 right-1/4 w-48 h-48 bg-[#B880B8]/30 rounded-full blur-3xl animate-float"
          style={{ animationDelay: "-3s" }}
        />

        {/* Content */}
        <div className="relative z-10 flex flex-col justify-center p-12 xl:p-16">
          <div className="max-w-md">
            <h2 className="text-3xl xl:text-4xl font-bold text-white mb-6 text-balance">
              Unlock the power of your BNPL data
            </h2>
            <p className="text-lg text-white/80 mb-8 leading-relaxed text-pretty">
              Get instant insights, risk analysis, and actionable recommendations
              through natural language queries.
            </p>

            {/* Feature list */}
            <div className="space-y-4">
              {[
                "Real-time KPI monitoring",
                "AI-powered risk explanations",
                "Role-based access control",
              ].map((feature) => (
                <div key={feature} className="flex items-center gap-3">
                  <div className="w-6 h-6 rounded-full bg-[#608818] flex items-center justify-center">
                    <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  </div>
                  <span className="text-white/90">{feature}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
