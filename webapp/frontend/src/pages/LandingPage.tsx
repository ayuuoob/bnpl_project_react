import { useState } from "react";
import { Link } from "react-router-dom";
import {
  MessageSquare,
  BarChart3,
  Briefcase,
  Database,
  CreditCard,
  Users,
  Warehouse,
  Zap,
  Shield,
  Eye,
  FileText,
  ChevronDown,
  Copy,
  Check,
  Menu,
  X,
  TrendingUp,
  AlertTriangle,
  Target,
  Lock,
  UserCheck,
  ClipboardList,
  ShieldCheck,
} from "lucide-react";

// Navbar Component
function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { href: "#product", label: "Product" },
    { href: "#how-it-works", label: "How it works" },
    { href: "#capabilities", label: "Capabilities" },
    { href: "#security", label: "Security" },
    { href: "#faq", label: "FAQ" },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-sm border-b border-[#505050]/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 lg:h-20">
          {/* Logo */}
          <Link
            to="/"
            className="flex items-center gap-3 text-lg sm:text-xl font-semibold text-[#303848] hover:text-[#582098] transition-colors"
          >
            <img
              src="/logo.png"
              alt="BNPL Copilot"
              width={56}
              height={56}
              className="h-14 w-14 object-contain"
            />
            <span className="hidden sm:inline">Intelligent BNPL Copilot</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden lg:flex items-center gap-8">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="text-sm font-medium text-[#505050] hover:text-[#582098] transition-colors"
              >
                {link.label}
              </a>
            ))}
          </div>

          {/* Desktop CTA */}
          <div className="hidden lg:flex items-center gap-4">
            <Link
              to="/login"
              className="text-sm font-medium text-[#505050] hover:text-[#582098] transition-colors"
            >
              Sign in
            </Link>
            <Link
              to="/request-access"
              className="px-5 py-2.5 bg-[#582098] text-white text-sm font-medium rounded-lg hover:bg-[#582098]/90 transition-all hover:shadow-lg hover:shadow-[#B880B8]/20"
            >
              Request access
            </Link>
          </div>

          {/* Mobile menu button */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-2 text-[#303848]"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="lg:hidden py-4 border-t border-[#505050]/10">
            <div className="flex flex-col gap-4">
              {navLinks.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className="text-sm font-medium text-[#505050] hover:text-[#582098] transition-colors"
                >
                  {link.label}
                </a>
              ))}
              <div className="flex flex-col gap-3 pt-4 border-t border-[#505050]/10">
                <Link
                  to="/login"
                  className="text-sm font-medium text-[#505050] hover:text-[#582098] transition-colors"
                >
                  Sign in
                </Link>
                <Link
                  to="/request-access"
                  className="px-5 py-2.5 bg-[#582098] text-white text-sm font-medium rounded-lg hover:bg-[#582098]/90 transition-all text-center"
                >
                  Request access
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}

// Hero Section with Product Mock
function HeroSection() {
  return (
    <section
      id="product"
      className="relative pt-24 lg:pt-32 pb-16 lg:pb-24 overflow-hidden"
    >
      {/* Background with subtle gradient and grid pattern */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#F8F8F8] via-white to-white" />
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fillRule='evenodd'%3E%3Cg fill='%23303848' fillOpacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
        }}
      />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Hero Content */}
        <div className="text-center max-w-4xl mx-auto mb-12 lg:mb-16">
          <h1 className="text-3xl sm:text-4xl lg:text-5xl xl:text-6xl font-bold text-[#303848] leading-tight mb-6 text-balance">
            Turn BNPL Data into Decisions Your Team Can Act On
          </h1>
          <p className="text-lg sm:text-xl text-[#505050] max-w-3xl mx-auto mb-8 leading-relaxed text-pretty">
            Ask questions in plain language and get instant KPIs, risk
            explanations, and recommended actions — grounded in your BNPL data.
          </p>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to="/login"
              className="w-full sm:w-auto px-8 py-3.5 bg-[#582098] text-white font-medium rounded-lg hover:bg-[#582098]/90 transition-all hover:shadow-xl hover:shadow-[#B880B8]/30 hover:-translate-y-0.5"
            >
              Sign in
            </Link>
            <Link
              to="/request-access"
              className="w-full sm:w-auto px-8 py-3.5 bg-white text-[#582098] font-medium rounded-lg border-2 border-[#582098] hover:bg-[#582098]/5 transition-all hover:-translate-y-0.5"
            >
              Request access
            </Link>
          </div>
        </div>

        {/* Product Screenshot Mock */}
        <ProductMock />

        {/* Try Example Prompts */}
        <div className="mt-8 text-center">
          <p className="text-sm text-[#505050] mb-3">Try example prompts</p>
          <div className="flex flex-wrap justify-center gap-2">
            {[
              "Show delinquency trends",
              "Top risky merchants",
              "Weekly approval rates",
            ].map((prompt) => (
              <a
                key={prompt}
                href="#examples"
                className="px-4 py-2 text-sm bg-[#F8F8F8] text-[#505050] rounded-full border border-[#505050]/10 hover:border-[#582098]/30 hover:text-[#582098] transition-all"
              >
                {prompt}
              </a>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

// Product Mock Component
function ProductMock() {
  return (
    <div className="relative max-w-5xl mx-auto">
      {/* Glow effect */}
      <div className="absolute inset-0 bg-gradient-to-r from-[#B880B8]/20 via-[#582098]/10 to-[#B880B8]/20 blur-3xl -z-10 scale-105" />

      {/* Main container */}
      <div className="bg-white rounded-2xl border border-[#505050]/10 shadow-2xl shadow-[#582098]/10 overflow-hidden">
        {/* Browser chrome */}
        <div className="flex items-center gap-2 px-4 py-3 bg-[#F8F8F8] border-b border-[#505050]/10">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-[#505050]/20" />
            <div className="w-3 h-3 rounded-full bg-[#505050]/20" />
            <div className="w-3 h-3 rounded-full bg-[#505050]/20" />
          </div>
          <div className="flex-1 mx-4">
            <div className="max-w-md mx-auto bg-white rounded-md px-3 py-1.5 text-xs text-[#505050]/60 border border-[#505050]/10">
              app.bnpl-copilot.internal
            </div>
          </div>
        </div>

        {/* App content */}
        <div className="flex min-h-[400px] lg:min-h-[480px]">
          {/* Left sidebar */}
          <div className="hidden sm:flex flex-col w-16 lg:w-56 bg-[#F8F8F8] border-r border-[#505050]/10 p-3 lg:p-4">
            {[
              { icon: MessageSquare, label: "Chat", active: true },
              { icon: BarChart3, label: "Analytics", active: false },
              { icon: Briefcase, label: "Cases", active: false },
            ].map((item) => (
              <div
                key={item.label}
                className={`flex items-center gap-3 p-2 lg:px-3 lg:py-2.5 rounded-lg mb-1 transition-colors ${
                  item.active
                    ? "bg-[#582098] text-white"
                    : "text-[#505050] hover:bg-white"
                }`}
              >
                <item.icon size={18} />
                <span className="hidden lg:inline text-sm font-medium">
                  {item.label}
                </span>
              </div>
            ))}
          </div>

          {/* Main chat area */}
          <div className="flex-1 flex flex-col p-4 lg:p-6">
            <div className="flex-1 space-y-4">
              {/* User message */}
              <div className="flex justify-end">
                <div className="max-w-[80%] bg-[#582098] text-white px-4 py-3 rounded-2xl rounded-br-md">
                  <p className="text-sm">
                    What changed in delinquency rate this week vs last week?
                  </p>
                </div>
              </div>

              {/* AI response */}
              <div className="flex justify-start">
                <div className="max-w-[85%] bg-[#F8F8F8] px-4 py-3 rounded-2xl rounded-bl-md border border-[#505050]/10">
                  <p className="text-sm text-[#303848] mb-3">
                    Delinquency rate increased by{" "}
                    <span className="font-semibold text-[#582098]">+0.8%</span>{" "}
                    this week (from 4.2% to 5.0%). Key drivers:
                  </p>
                  <ul className="text-sm text-[#505050] space-y-1.5 ml-4">
                    <li className="flex items-start gap-2">
                      <span className="text-[#608818] mt-0.5">•</span>
                      <span>
                        Merchant ID{" "}
                        <code className="text-xs bg-white px-1 py-0.5 rounded">
                          m_0042
                        </code>{" "}
                        accounts for 35% of new late payments
                      </span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-[#608818] mt-0.5">•</span>
                      <span>Users with {"<"}3 months tenure show 2.1x higher risk</span>
                    </li>
                  </ul>
                  <div className="mt-3 pt-3 border-t border-[#505050]/10">
                    <p className="text-xs text-[#505050] flex items-center gap-1">
                      <Shield size={12} className="text-[#608818]" />
                      Based on 12,847 installments analyzed
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Input area */}
            <div className="mt-4 flex items-center gap-2 bg-[#F8F8F8] rounded-xl px-4 py-3 border border-[#505050]/10">
              <input
                type="text"
                placeholder="Ask about your BNPL data..."
                className="flex-1 bg-transparent text-sm text-[#303848] placeholder-[#505050]/50 outline-none"
                readOnly
              />
              <button
                type="button"
                className="p-2 bg-[#582098] text-white rounded-lg hover:bg-[#582098]/90 transition-colors"
              >
                <Zap size={16} />
              </button>
            </div>
          </div>

          {/* Right insights panel */}
          <div className="hidden lg:flex flex-col w-64 bg-[#F8F8F8] border-l border-[#505050]/10 p-4">
            <h3 className="text-xs font-semibold text-[#505050] uppercase tracking-wider mb-4">
              Live Insights
            </h3>

            {/* KPI cards */}
            <div className="space-y-3">
              {[
                {
                  label: "Delinquency Rate",
                  value: "5.0%",
                  trend: "+0.8%",
                  negative: true,
                },
                {
                  label: "Approval Rate",
                  value: "72.3%",
                  trend: "+2.1%",
                  negative: false,
                },
                {
                  label: "Avg Order Value",
                  value: "$284",
                  trend: "-$12",
                  negative: true,
                },
              ].map((kpi) => (
                <div
                  key={kpi.label}
                  className="bg-white rounded-lg p-3 border border-[#505050]/10"
                >
                  <p className="text-xs text-[#505050] mb-1">{kpi.label}</p>
                  <div className="flex items-end justify-between">
                    <span className="text-lg font-semibold text-[#303848]">
                      {kpi.value}
                    </span>
                    <span
                      className={`text-xs font-medium ${
                        kpi.negative ? "text-[#582098]" : "text-[#608818]"
                      }`}
                    >
                      {kpi.trend}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {/* Mini chart placeholder */}
            <div className="mt-4 bg-white rounded-lg p-3 border border-[#505050]/10">
              <p className="text-xs text-[#505050] mb-2">Weekly Trend</p>
              <div className="flex items-end justify-between h-16 gap-1">
                {[40, 35, 45, 50, 42, 55, 60].map((h, i) => (
                  <div
                    key={i}
                    className="flex-1 bg-gradient-to-t from-[#582098] to-[#B880B8] rounded-t"
                    style={{ height: `${h}%` }}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Schema/Diagram Section
function SchemaSection() {
  return (
    <section id="how-it-works" className="py-16 lg:py-24 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section header */}
        <div className="text-center max-w-3xl mx-auto mb-12 lg:mb-16">
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-[#303848] mb-4 text-balance">
            How Intelligent BNPL Copilot Creates Business Impact
          </h2>
          <p className="text-lg text-[#505050] text-pretty">
            We don't add more dashboards. We turn your BNPL data into fast
            answers, clear explanations, and actions.
          </p>
        </div>

        {/* Flow Diagram */}
        {/* (unchanged from your code) */}
        {/* NOTE: Keeping everything as-is below */}
        <div className="relative mb-16 lg:mb-20">
          {/* Desktop flow diagram */}
          <div className="hidden lg:block">
            <div className="flex items-center justify-between gap-4">
              {/* Data Sources */}
              <div className="flex flex-col gap-3">
                {[
                  { icon: CreditCard, label: "BNPL App" },
                  { icon: Database, label: "Payments" },
                  { icon: Users, label: "CRM" },
                  { icon: Warehouse, label: "Data Warehouse" },
                ].map((source) => (
                  <div
                    key={source.label}
                    className="flex items-center gap-3 bg-[#F8F8F8] rounded-full px-4 py-2.5 border border-[#505050]/10"
                  >
                    <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center border border-[#505050]/10">
                      <source.icon size={18} className="text-[#582098]" />
                    </div>
                    <span className="text-sm font-medium text-[#303848]">
                      {source.label}
                    </span>
                  </div>
                ))}
              </div>

              {/* Connector line */}
              <div className="flex-1 max-w-[80px] h-0.5 bg-gradient-to-r from-[#505050]/20 to-[#582098]/50" />

              {/* Central Node */}
              <div className="relative">
                <div className="absolute inset-0 bg-[#B880B8]/20 rounded-2xl blur-xl animate-pulse" />
                <div className="relative bg-gradient-to-br from-[#582098] to-[#582098]/80 text-white rounded-2xl p-6 text-center shadow-lg shadow-[#582098]/20 animate-pulse-glow">
                  <Database size={32} className="mx-auto mb-2" />
                  <p className="text-sm font-semibold">Your BNPL Data</p>
                  <p className="text-xs opacity-80">Foundation</p>
                </div>
              </div>

              {/* Connector line */}
              <div className="flex-1 max-w-[60px] h-0.5 bg-gradient-to-r from-[#582098]/50 to-[#505050]/20" />

              {/* Prompt Card */}
              <div className="bg-white rounded-xl border border-[#505050]/10 p-4 shadow-lg max-w-xs">
                <div className="bg-[#F8F8F8] rounded-lg px-3 py-2 mb-3 border border-[#505050]/10">
                  <p className="text-xs text-[#505050]">Prompt:</p>
                  <p className="text-sm text-[#303848] font-medium">
                    "Show me late-payment risk trends for the last 6 months"
                  </p>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {[
                    "gold_orders_analytics",
                    "uc1_scored_today",
                    "explanations",
                  ].map((pill) => (
                    <span
                      key={pill}
                      className="px-2 py-1 bg-[#582098]/10 text-[#582098] text-xs rounded-md font-mono"
                    >
                      {pill}
                    </span>
                  ))}
                </div>
              </div>

              {/* Connector line */}
              <div className="flex-1 max-w-[60px] h-0.5 bg-gradient-to-r from-[#505050]/20 to-[#608818]/50" />

              {/* Outcome Cards */}
              <div className="flex flex-col gap-3">
                {[
                  { icon: Eye, label: "Proactive Monitoring", color: "#608818" },
                  {
                    icon: Target,
                    label: "Action Recommendations",
                    color: "#582098",
                  },
                  { icon: Zap, label: "Operational Automation", color: "#582098" },
                ].map((outcome) => (
                  <div
                    key={outcome.label}
                    className="flex items-center gap-3 bg-white rounded-lg px-4 py-3 border border-[#505050]/10 shadow-sm hover:shadow-md hover:border-[#582098]/20 transition-all"
                  >
                    <div
                      className="w-8 h-8 rounded-lg flex items-center justify-center"
                      style={{ backgroundColor: `${outcome.color}15` }}
                    >
                      <outcome.icon size={16} style={{ color: outcome.color }} />
                    </div>
                    <span className="text-sm font-medium text-[#303848]">
                      {outcome.label}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Mobile flow diagram - simplified vertical */}
          <div className="lg:hidden space-y-6">
            {/* Data Sources */}
            <div className="bg-[#F8F8F8] rounded-xl p-4 border border-[#505050]/10">
              <p className="text-xs font-semibold text-[#505050] uppercase tracking-wider mb-3">
                Data Sources
              </p>
              <div className="flex flex-wrap gap-2">
                {[
                  { icon: CreditCard, label: "BNPL App" },
                  { icon: Database, label: "Payments" },
                  { icon: Users, label: "CRM" },
                  { icon: Warehouse, label: "Data Warehouse" },
                ].map((source) => (
                  <div
                    key={source.label}
                    className="flex items-center gap-2 bg-white rounded-full px-3 py-1.5 border border-[#505050]/10"
                  >
                    <source.icon size={14} className="text-[#582098]" />
                    <span className="text-xs font-medium text-[#303848]">
                      {source.label}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Arrow */}
            <div className="flex justify-center">
              <ChevronDown size={24} className="text-[#582098]" />
            </div>

            {/* Central Node */}
            <div className="bg-gradient-to-br from-[#582098] to-[#582098]/80 text-white rounded-xl p-4 text-center shadow-lg shadow-[#582098]/20">
              <Database size={24} className="mx-auto mb-2" />
              <p className="text-sm font-semibold">Your BNPL Data Foundation</p>
            </div>

            {/* Arrow */}
            <div className="flex justify-center">
              <ChevronDown size={24} className="text-[#582098]" />
            </div>

            {/* Prompt */}
            <div className="bg-white rounded-xl border border-[#505050]/10 p-4 shadow-sm">
              <p className="text-xs text-[#505050] mb-1">Prompt:</p>
              <p className="text-sm text-[#303848] font-medium mb-3">
                "Show me late-payment risk trends for the last 6 months"
              </p>
              <div className="flex flex-wrap gap-1.5">
                {["gold_orders_analytics", "uc1_scored_today"].map((pill) => (
                  <span
                    key={pill}
                    className="px-2 py-1 bg-[#582098]/10 text-[#582098] text-xs rounded-md font-mono"
                  >
                    {pill}
                  </span>
                ))}
              </div>
            </div>

            {/* Arrow */}
            <div className="flex justify-center">
              <ChevronDown size={24} className="text-[#608818]" />
            </div>

            {/* Outcomes */}
            <div className="space-y-2">
              {[
                { icon: Eye, label: "Proactive Monitoring" },
                { icon: Target, label: "Action Recommendations" },
                { icon: Zap, label: "Operational Automation" },
              ].map((outcome) => (
                <div
                  key={outcome.label}
                  className="flex items-center gap-3 bg-[#F8F8F8] rounded-lg px-4 py-3 border border-[#505050]/10"
                >
                  <outcome.icon size={18} className="text-[#608818]" />
                  <span className="text-sm font-medium text-[#303848]">
                    {outcome.label}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* How It Works Cards */}
        <div className="grid md:grid-cols-3 gap-6 lg:gap-8">
          {[
            {
              step: "01",
              title: "Ask in Natural Language",
              description:
                "No SQL, no dashboards required. Ask your questions like you would to a colleague.",
              icon: MessageSquare,
            },
            {
              step: "02",
              title: "Get Instant Insights",
              description:
                "KPIs, trends, and risk signals delivered instantly with visual analytics.",
              icon: BarChart3,
            },
            {
              step: "03",
              title: "Act with Confidence",
              description:
                "Operational and strategic guidance based on real BNPL data.",
              icon: Target,
            },
          ].map((item) => (
            <div
              key={item.step}
              className="group bg-white rounded-2xl p-6 lg:p-8 border border-[#505050]/10 hover:border-[#582098]/20 hover:shadow-xl hover:shadow-[#B880B8]/10 transition-all"
            >
              <div className="flex items-center gap-4 mb-4">
                <div className="w-12 h-12 rounded-xl bg-[#582098]/10 flex items-center justify-center group-hover:bg-[#582098] transition-colors">
                  <item.icon
                    size={22}
                    className="text-[#582098] group-hover:text-white transition-colors"
                  />
                </div>
                <span className="text-3xl font-bold text-[#582098]/20 group-hover:text-[#582098]/40 transition-colors">
                  {item.step}
                </span>
              </div>
              <h3 className="text-lg font-semibold text-[#303848] mb-2">
                {item.title}
              </h3>
              <p className="text-[#505050] text-sm leading-relaxed">
                {item.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// Capabilities Section
function CapabilitiesSection() {
  const capabilities = [
    {
      icon: TrendingUp,
      title: "Portfolio KPIs & trends",
      description:
        "Track approval rates, delinquency, and performance metrics in real-time.",
    },
    {
      icon: AlertTriangle,
      title: "Risk explanations (not just scores)",
      description:
        "Understand why an account is flagged with clear, traceable reasoning.",
    },
    {
      icon: Users,
      title: "Drill down by entity",
      description:
        "Explore data by user, order, merchant, or installment with natural queries.",
    },
    {
      icon: Target,
      title: "Recommendations & next steps",
      description:
        "Get actionable guidance based on patterns in your BNPL data.",
    },
    {
      icon: Eye,
      title: "Monitoring & early warning signals",
      description:
        "Proactive alerts when metrics deviate from expected baselines.",
    },
    {
      icon: FileText,
      title: "Analyst-ready exports",
      description:
        "Tables, snapshots, and reports ready for downstream analysis.",
    },
  ];

  return (
    <section id="capabilities" className="py-16 lg:py-24 bg-[#F8F8F8]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-12 lg:mb-16">
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-[#303848] mb-4">
            Capabilities
          </h2>
          <p className="text-lg text-[#505050]">
            Everything your BNPL team needs to move from data to decisions.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {capabilities.map((cap) => (
            <div
              key={cap.title}
              className="bg-white rounded-xl p-6 border border-[#505050]/10 hover:border-[#582098]/20 hover:shadow-lg hover:shadow-[#B880B8]/10 transition-all group"
            >
              <div className="w-12 h-12 rounded-xl bg-[#582098]/10 flex items-center justify-center mb-4 group-hover:bg-[#582098] transition-colors">
                <cap.icon
                  size={22}
                  className="text-[#582098] group-hover:text-white transition-colors"
                />
              </div>
              <h3 className="text-base font-semibold text-[#303848] mb-2">
                {cap.title}
              </h3>
              <p className="text-sm text-[#505050] leading-relaxed">
                {cap.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// Examples Section
function ExamplesSection() {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const prompts = [
    "What changed in delinquency rate this week vs last week?",
    "Show the top 10 merchants driving late payments.",
    "Why is inst_0000141 flagged as risky?",
    "Which users are likely to pay late before the due date?",
    "Give me the weekly trend of approvals and defaults.",
  ];

  const copyToClipboard = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <section id="examples" className="py-16 lg:py-24 bg-white">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-[#303848] mb-4">
            Try These Examples
          </h2>
          <p className="text-lg text-[#505050]">
            Click to copy any prompt and see what insights you can unlock.
          </p>
        </div>

        <div className="space-y-3">
          {prompts.map((prompt, index) => (
            <button
              key={prompt}
              type="button"
              onClick={() => copyToClipboard(prompt, index)}
              className="w-full flex items-center justify-between gap-4 bg-[#F8F8F8] hover:bg-[#582098]/5 rounded-xl px-5 py-4 border border-[#505050]/10 hover:border-[#582098]/30 transition-all text-left group"
            >
              <span className="text-sm sm:text-base text-[#303848] group-hover:text-[#582098] transition-colors">
                "{prompt}"
              </span>
              <div className="flex-shrink-0">
                {copiedIndex === index ? (
                  <div className="flex items-center gap-1 text-[#608818]">
                    <Check size={16} />
                    <span className="text-xs font-medium">Copied</span>
                  </div>
                ) : (
                  <Copy
                    size={16}
                    className="text-[#505050] group-hover:text-[#582098] transition-colors"
                  />
                )}
              </div>
            </button>
          ))}
        </div>

        <p className="text-center text-sm text-[#505050] mt-8">
          Built for BNPL teams who want insights fast. No data science required.
        </p>
      </div>
    </section>
  );
}

// Security Section
function SecuritySection() {
  const features = [
    {
      icon: Lock,
      title: "Authentication required (SSO-ready)",
      description:
        "Enterprise-grade authentication with single sign-on support.",
    },
    {
      icon: UserCheck,
      title: "Role-based access control (RBAC)",
      description:
        "Granular permissions ensure the right people see the right data.",
    },
    {
      icon: ClipboardList,
      title: "Audit logs (question → data → answer)",
     description:
        "Complete traceability from every query to its data sources.",
    },
    {
      icon: ShieldCheck,
      title: "Data privacy aligned with internal policies",
      description: "Your data stays within your security perimeter.",
    },
  ];

  return (
    <section id="security" className="py-16 lg:py-24 bg-[#F8F8F8]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-12 lg:mb-16">
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-[#303848] mb-4">
            Security & Governance
          </h2>
          <p className="text-lg text-[#505050]">
            Enterprise-grade security for your most sensitive BNPL data.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 gap-6 max-w-4xl mx-auto">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="flex gap-4 bg-white rounded-xl p-6 border border-[#505050]/10"
            >
              <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-[#608818]/10 flex items-center justify-center">
                <feature.icon size={22} className="text-[#608818]" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-[#303848] mb-1">
                  {feature.title}
                </h3>
                <p className="text-sm text-[#505050] leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// FAQ Section
function FAQSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  const faqs = [
    {
      question: "Is this a public SaaS?",
      answer:
        "No. Intelligent BNPL Copilot is an internal/enterprise tool. It's designed for BNPL owner companies or agencies to use with their own data, within their own security perimeter.",
    },
    {
      question: "Does it replace dashboards?",
      answer:
        "Not necessarily. It complements existing dashboards by providing a conversational interface to your data. Teams can get quick answers without waiting for scheduled reports or building new dashboard views.",
    },
    {
      question: "Can it show charts/tables?",
      answer:
        "Yes. The Copilot can generate visual analytics including charts, tables, and trend visualizations as part of its responses. It can also export analyst-ready tables and snapshots.",
    },
    {
      question: "How do you prevent made-up answers?",
      answer:
        "Every insight is grounded in your actual BNPL data with full traceability. The system shows which data sources were used and provides clear reasoning chains from question to answer.",
    },
    {
      question: "Who can access it?",
      answer:
        "Access is controlled through your organization's authentication (SSO-ready) and role-based access control. Only authorized team members can query the data they're permitted to see.",
    },
    {
      question: "Can we integrate it into existing tools?",
      answer:
        "Yes. The Copilot can be embedded into your existing workflows through APIs, and insights can be accessed through collaboration platforms your teams already use.",
    },
  ];

  return (
    <section id="faq" className="py-16 lg:py-24 bg-white">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-[#303848] mb-4">
            Frequently Asked Questions
          </h2>
        </div>

        <div className="space-y-3">
          {faqs.map((faq, index) => (
            <div
              key={faq.question}
              className="bg-[#F8F8F8] rounded-xl border border-[#505050]/10 overflow-hidden"
            >
              <button
                type="button"
                onClick={() => setOpenIndex(openIndex === index ? null : index)}
                className="w-full flex items-center justify-between gap-4 px-6 py-4 text-left"
              >
                <span className="font-medium text-[#303848]">{faq.question}</span>
                <ChevronDown
                  size={20}
                  className={`flex-shrink-0 text-[#505050] transition-transform ${
                    openIndex === index ? "rotate-180" : ""
                  }`}
                />
              </button>
              {openIndex === index && (
                <div className="px-6 pb-4">
                  <p className="text-sm text-[#505050] leading-relaxed">
                    {faq.answer}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// CTA Banner
function CTABanner() {
  return (
    <section className="py-16 lg:py-24 bg-gradient-to-br from-[#582098] to-[#582098]/90">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-white mb-6 text-balance">
          Ready to turn BNPL data into decisions?
        </h2>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            to="/login"
            className="w-full sm:w-auto px-8 py-3.5 bg-white text-[#582098] font-medium rounded-lg hover:bg-white/90 transition-all hover:shadow-xl"
          >
            Sign in
          </Link>
          <Link
            to="/request-access"
            className="w-full sm:w-auto px-8 py-3.5 bg-transparent text-white font-medium rounded-lg border-2 border-white hover:bg-white/10 transition-all"
          >
            Request access
          </Link>
        </div>
      </div>
    </section>
  );
}

// Footer
function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="py-8 bg-white border-t border-[#505050]/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center gap-3">
          <div className="flex items-center gap-2">
            <img
              src="/logo.png"
              alt="BNPL Copilot"
              width={32}
              height={32}
              className="h-8 w-8 object-contain"
            />
            <span className="text-sm font-medium text-[#303848]">
              Intelligent BNPL Copilot
            </span>
          </div>
          <p className="text-center text-sm text-[#505050]">
            © {currentYear} Intelligent BNPL Copilot. Internal use only.
          </p>
        </div>
      </div>
    </footer>
  );
}

// Main Page
export default function LandingPage() {
  return (
    <main className="min-h-screen bg-white">
      <Navbar />
      <HeroSection />
      <SchemaSection />
      <CapabilitiesSection />
      <ExamplesSection />
      <SecuritySection />
      <FAQSection />
      <CTABanner />
      <Footer />
    </main>
  );
}
