import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  getCurrentUser,
  hasPermission,
  type User,
  type Permission,
} from "../lib/auth";
import { AppNavbar } from "../components/AppNavbar";
import {
  Users,
  DollarSign,
  AlertTriangle,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  BarChart3,
  PieChart,
  Clock,
  CheckCircle2,
  XCircle,
  Shield,
  TableIcon,
} from "lucide-react";

const API_BASE = "http://localhost:8002";

interface KPIData {
  gmv: { value: number; formatted: string; change: string; trend: string };
  activeUsers: { value: number; formatted: string; change: string; trend: string };
  defaultRate: { value: number; formatted: string; change: string; trend: string };
  approvalRate: { value: number; formatted: string; change: string; trend: string };
}

interface RiskCityData {
  city: string;
  highRisk: number;
  lowRisk: number;
  total: number;
  avgRiskProb: number;
}

interface PortfolioData {
  onTime: { value: number; formatted: string };
  late: { value: number; formatted: string };
  defaults: { value: number; formatted: string };
}

interface RiskyUser {
  userId: string;
  city: string;
  dueDate: string;
  riskPct: number;
  lateRatePct: number;
  activePlans: number;
  status: string;
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [kpis, setKpis] = useState<KPIData | null>(null);
  const [riskDistribution, setRiskDistribution] = useState<RiskCityData[]>([]);
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);
  const [riskyUsers, setRiskyUsers] = useState<RiskyUser[]>([]);

  useEffect(() => {
    const currentUser = getCurrentUser();
    if (!currentUser) {
      navigate("/login", { replace: true });
    } else {
      setUser(currentUser);
    }
  }, [navigate]);

  useEffect(() => {
    async function fetchDashboardData() {
      try {
        const [kpisRes, riskRes, portfolioRes, riskyUsersRes] = await Promise.all([
          fetch(`${API_BASE}/api/dashboard/kpis`),
          fetch(`${API_BASE}/api/dashboard/risk-distribution`),
          fetch(`${API_BASE}/api/dashboard/portfolio`),
          fetch(`${API_BASE}/api/dashboard/risky-users`),
        ]);

        if (kpisRes.ok) {
          const kpisData = await kpisRes.json();
          setKpis(kpisData);
        }

        if (riskRes.ok) {
          const riskData = await riskRes.json();
          setRiskDistribution(riskData);
        }

        if (portfolioRes.ok) {
          const portfolioData = await portfolioRes.json();
          setPortfolio(portfolioData);
        }

        if (riskyUsersRes.ok) {
          const riskyUsersData = await riskyUsersRes.json();
          setRiskyUsers(riskyUsersData);
        }
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
      }
    }

    fetchDashboardData();
  }, []);

  if (!user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#F8F8F8]">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-[#582098] border-t-transparent" />
      </div>
    );
  }

  const kpiCards = [
    {
      title: "Total GMV",
      value: kpis?.gmv.formatted ?? "Loading...",
      change: kpis?.gmv.change ?? "+0%",
      trend: (kpis?.gmv.trend ?? "up") as "up" | "down",
      icon: DollarSign,
      color: "#582098",
    },
    {
      title: "Active Users",
      value: kpis?.activeUsers.formatted ?? "Loading...",
      change: kpis?.activeUsers.change ?? "+0%",
      trend: (kpis?.activeUsers.trend ?? "up") as "up" | "down",
      icon: Users,
      color: "#608818",
    },
    {
      title: "Default Rate",
      value: kpis?.defaultRate.formatted ?? "Loading...",
      change: kpis?.defaultRate.change ?? "+0%",
      trend: (kpis?.defaultRate.trend ?? "down") as "up" | "down",
      icon: AlertTriangle,
      color: "#dc2626",
    },
    {
      title: "Approval Rate",
      value: kpis?.approvalRate.formatted ?? "Loading...",
      change: kpis?.approvalRate.change ?? "+0%",
      trend: (kpis?.approvalRate.trend ?? "up") as "up" | "down",
      icon: Activity,
      color: "#582098",
    },
  ];

  const recentActivity = [
    {
      action: "High-risk alert",
      detail: "User 00497 flagged for review",
      time: "2 min ago",
      type: "warning" as const,
    },
    {
      action: "Limit adjusted",
      detail: "User 00233 limit decreased to 1600",
      time: "15 min ago",
      type: "info" as const,
    },
    {
      action: "New merchant",
      detail: "TechStore Casablanca onboarded",
      time: "1 hour ago",
      type: "success" as const,
    },
    {
      action: "Report generated",
      detail: "Monthly risk assessment Q4",
      time: "3 hours ago",
      type: "info" as const,
    },
  ];

  const permissions: Permission[] = [
    "view_dashboard",
    "view_analytics",
    "export_data",
    "manage_users",
    "configure_system",
    "view_audit_logs",
  ];

  return (
    <div className="min-h-screen bg-[#F8F8F8]">
      <AppNavbar />

      <main className="p-6">
        <div className="mx-auto max-w-7xl">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-2xl font-semibold text-[#303848]">
              Welcome back, {user.name}
            </h1>
            <p className="mt-1 text-[#505050]">
              Here&apos;s what&apos;s happening with your BNPL portfolio today.
            </p>
          </div>

          {/* KPI Cards */}
          <div className="mb-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {kpiCards.map((kpi) => (
              <div
                key={kpi.title}
                className="rounded-xl border border-border bg-white p-6 shadow-sm transition-shadow hover:shadow-md"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm font-medium text-[#505050]">
                      {kpi.title}
                    </p>
                    <p className="mt-2 text-2xl font-semibold text-[#303848]">
                      {kpi.value}
                    </p>
                  </div>
                  <div
                    className="rounded-lg p-2"
                    style={{ backgroundColor: `${kpi.color}15` }}
                  >
                    <kpi.icon className="h-5 w-5" style={{ color: kpi.color }} />
                  </div>
                </div>
                <div className="mt-4 flex items-center gap-1">
                  {kpi.trend === "up" ? (
                    <ArrowUpRight className="h-4 w-4 text-[#608818]" />
                  ) : (
                    <ArrowDownRight className="h-4 w-4 text-[#dc2626]" />
                  )}
                  <span
                    className={`text-sm font-medium ${
                      kpi.trend === "up" ? "text-[#608818]" : "text-[#dc2626]"
                    }`}
                  >
                    {kpi.change}
                  </span>
                  <span className="text-sm text-[#505050]">vs last month</span>
                </div>
              </div>
            ))}
          </div>

          <div className="grid gap-6 lg:grid-cols-3">
            {/* Charts Section */}
            <div className="lg:col-span-2 space-y-6">
              {/* Risk Distribution Chart */}
              <div className="rounded-xl border border-border bg-white p-6 shadow-sm">
                <div className="mb-6 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5 text-[#582098]" />
                    <h2 className="font-semibold text-[#303848]">
                      Risk Distribution by Region
                    </h2>
                  </div>
                  <select className="rounded-lg border border-border bg-white px-3 py-1.5 text-sm text-[#505050]">
                    <option>Last 30 days</option>
                    <option>Last 90 days</option>
                    <option>This year</option>
                  </select>
                </div>

                <div className="flex h-64 items-end justify-around gap-4">
                  {riskDistribution.length > 0 ? (
                    riskDistribution.map((data) => {
                      const maxTotal = Math.max(...riskDistribution.map(d => d.total));
                      const scale = 180 / maxTotal; // Scale to fit in chart
                      return (
                        <div
                          key={data.city}
                          className="flex flex-1 flex-col items-center gap-2"
                        >
                          <div className="flex w-full max-w-[60px] flex-col gap-1">
                            <div
                              className="w-full rounded-t bg-[#dc2626]/80"
                              style={{ height: `${data.highRisk * scale}px` }}
                            />
                            <div
                              className="w-full rounded-b bg-[#582098]"
                              style={{ height: `${data.lowRisk * scale}px` }}
                            />
                          </div>
                          <span className="text-xs text-[#505050]">{data.city}</span>
                        </div>
                      );
                    })
                  ) : (
                    <div className="flex h-full w-full items-center justify-center">
                      <div className="h-6 w-6 animate-spin rounded-full border-2 border-[#582098] border-t-transparent" />
                    </div>
                  )}
                </div>

                <div className="mt-4 flex items-center justify-center gap-6">
                  <div className="flex items-center gap-2">
                    <div className="h-3 w-3 rounded bg-[#dc2626]/80" />
                    <span className="text-sm text-[#505050]">High Risk</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="h-3 w-3 rounded bg-[#582098]" />
                    <span className="text-sm text-[#505050]">Low Risk</span>
                  </div>
                </div>
              </div>

              {/* Portfolio Overview */}
              <div className="rounded-xl border border-border bg-white p-6 shadow-sm">
                <div className="mb-6 flex items-center gap-2">
                  <PieChart className="h-5 w-5 text-[#582098]" />
                  <h2 className="font-semibold text-[#303848]">
                    Portfolio Overview
                  </h2>
                </div>

                <div className="grid gap-4 sm:grid-cols-3">
                  {portfolio ? (
                    [
                      { label: "On-time payments", value: portfolio.onTime.formatted, color: "#608818" },
                      { label: "Late payments", value: portfolio.late.formatted, color: "#f59e0b" },
                      { label: "Unpaid payments", value: portfolio.defaults.formatted, color: "#dc2626" },
                    ].map((item) => (
                      <div
                        key={item.label}
                        className="rounded-lg border border-border p-4"
                      >
                        <div className="mb-2 flex items-center justify-between">
                          <span className="text-sm text-[#505050]">
                            {item.label}
                          </span>
                          <span
                            className="text-lg font-semibold"
                            style={{ color: item.color }}
                          >
                            {item.value}
                          </span>
                        </div>
                        <div className="h-2 w-full overflow-hidden rounded-full bg-[#F8F8F8]">
                          <div
                            className="h-full rounded-full"
                            style={{
                              width: item.value,
                              backgroundColor: item.color,
                            }}
                          />
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="col-span-3 flex items-center justify-center py-8">
                      <div className="h-6 w-6 animate-spin rounded-full border-2 border-[#582098] border-t-transparent" />
                    </div>
                  )}
                </div>
              </div>

              {/* Risky Users Table */}
              <div className="rounded-xl border border-border bg-white p-6 shadow-sm">
                <div className="mb-6 flex items-center gap-2">
                  <TableIcon className="h-5 w-5 text-[#582098]" />
                  <h2 className="font-semibold text-[#303848]">
                    Users at Risk of Late Payment
                  </h2>
                </div>

                <div className="overflow-x-auto">
                  {riskyUsers.length > 0 ? (
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-border">
                          <th className="pb-3 text-left font-medium text-[#505050]">User ID</th>
                          <th className="pb-3 text-left font-medium text-[#505050]">City</th>
                          <th className="pb-3 text-left font-medium text-[#505050]">Due Date</th>
                          <th className="pb-3 text-right font-medium text-[#505050]">Risk %</th>
                          <th className="pb-3 text-right font-medium text-[#505050]">Late Rate</th>
                          <th className="pb-3 text-center font-medium text-[#505050]">Plans</th>
                        </tr>
                      </thead>
                      <tbody>
                        {riskyUsers.map((user, index) => (
                          <tr
                            key={`${user.userId}-${index}`}
                            className="border-b border-border/50 last:border-0"
                          >
                            <td className="py-3 font-medium text-[#303848]">
                              {user.userId}
                            </td>
                            <td className="py-3 text-[#505050]">{user.city}</td>
                            <td className="py-3 text-[#505050]">{user.dueDate}</td>
                            <td className="py-3 text-right">
                              <span
                                className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                                  user.riskPct >= 40
                                    ? "bg-[#dc2626]/10 text-[#dc2626]"
                                    : user.riskPct >= 25
                                    ? "bg-[#f59e0b]/10 text-[#f59e0b]"
                                    : "bg-[#608818]/10 text-[#608818]"
                                }`}
                              >
                                {user.riskPct}%
                              </span>
                            </td>
                            <td className="py-3 text-right text-[#505050]">
                              {user.lateRatePct}%
                            </td>
                            <td className="py-3 text-center text-[#505050]">
                              {user.activePlans}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <div className="flex items-center justify-center py-8">
                      <div className="h-6 w-6 animate-spin rounded-full border-2 border-[#582098] border-t-transparent" />
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Right Column */}
            <div className="space-y-6">
              {/* Recent Activity */}
              <div className="rounded-xl border border-border bg-white p-6 shadow-sm">
                <div className="mb-4 flex items-center gap-2">
                  <Clock className="h-5 w-5 text-[#582098]" />
                  <h2 className="font-semibold text-[#303848]">
                    Recent Activity
                  </h2>
                </div>

                <div className="space-y-4">
                  {recentActivity.map((item, index) => (
                    <div key={index} className="flex items-start gap-3">
                      <div
                        className={`mt-0.5 rounded-full p-1 ${
                          item.type === "warning"
                            ? "bg-[#f59e0b]/10"
                            : item.type === "success"
                            ? "bg-[#608818]/10"
                            : "bg-[#582098]/10"
                        }`}
                      >
                        {item.type === "warning" ? (
                          <AlertTriangle className="h-3 w-3 text-[#f59e0b]" />
                        ) : item.type === "success" ? (
                          <CheckCircle2 className="h-3 w-3 text-[#608818]" />
                        ) : (
                          <Activity className="h-3 w-3 text-[#582098]" />
                        )}
                      </div>

                      <div className="flex-1">
                        <p className="text-sm font-medium text-[#303848]">
                          {item.action}
                        </p>
                        <p className="text-xs text-[#505050]">{item.detail}</p>
                        <p className="mt-1 text-xs text-[#505050]/70">
                          {item.time}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Permissions */}
              <div className="rounded-xl border border-border bg-white p-6 shadow-sm">
                <div className="mb-4 flex items-center gap-2">
                  <Shield className="h-5 w-5 text-[#582098]" />
                  <h2 className="font-semibold text-[#303848]">
                    Your Permissions
                  </h2>
                </div>

                <div className="space-y-2">
                  {permissions.map((permission) => {
                    const granted = hasPermission(user, permission);
                    return (
                      <div
                        key={permission}
                        className="flex items-center justify-between rounded-lg bg-[#F8F8F8] px-3 py-2"
                      >
                        <span className="text-sm capitalize text-[#303848]">
                          {permission.replace(/_/g, " ")}
                        </span>
                        {granted ? (
                          <CheckCircle2 className="h-4 w-4 text-[#608818]" />
                        ) : (
                          <XCircle className="h-4 w-4 text-[#dc2626]" />
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
