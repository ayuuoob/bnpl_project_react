import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { getCurrentUser, type User } from "../lib/auth";
import { AppNavbar } from "../components/AppNavbar";
import {
  BookOpen,
  MessageSquare,
  BarChart3,
  Search,
  Lightbulb,
  Zap,
  Target,
  ChevronRight,
  HelpCircle,
  Users,
  TrendingUp,
  AlertTriangle,
  Download,
  Shield,
} from "lucide-react";

export default function DocsPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams(); // keep if you later want deep-linking
  const [user, setUser] = useState<User | null>(null);
  const [activeSection, setActiveSection] = useState("getting-started");
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    const currentUser = getCurrentUser();
    if (!currentUser) {
      navigate("/login", { replace: true });
    } else {
      setUser(currentUser);
    }
  }, [navigate]);

  // OPTIONAL: deep-link support like /docs?section=faq
  useEffect(() => {
    const section = searchParams.get("section");
    if (section) setActiveSection(section);
  }, [searchParams]);

  const sections = useMemo(
    () => [
      {
        id: "getting-started",
        label: "Getting Started",
        icon: BookOpen,
        keywords: [
          "start",
          "begin",
          "introduction",
          "quick",
          "guide",
          "what is",
          "copilot",
          "overview",
          "accurate",
          "instant",
          "secure",
        ],
      },
      {
        id: "asking-questions",
        label: "Asking Questions",
        icon: MessageSquare,
        keywords: [
          "ask",
          "question",
          "query",
          "natural language",
          "follow-up",
          "conversation",
          "how to ask",
          "formulate",
        ],
      },
      {
        id: "understanding-analytics",
        label: "Understanding Analytics",
        icon: BarChart3,
        keywords: [
          "analytics",
          "panel",
          "charts",
          "metrics",
          "visualization",
          "overview",
          "details",
          "late rate",
          "risk score",
          "scored users",
          "kpi",
        ],
      },
      {
        id: "example-prompts",
        label: "Example Prompts",
        icon: Lightbulb,
        keywords: [
          "example",
          "prompt",
          "portfolio",
          "kpi",
          "risk",
          "analysis",
          "user",
          "insights",
          "exports",
          "reports",
          "gmv",
          "default",
          "risky",
        ],
      },
      {
        id: "tips-tricks",
        label: "Tips & Tricks",
        icon: Zap,
        keywords: [
          "tips",
          "tricks",
          "specific",
          "time frame",
          "explanation",
          "comparison",
          "best practices",
          "help",
        ],
      },
      {
        id: "faq",
        label: "FAQ",
        icon: HelpCircle,
        keywords: [
          "faq",
          "frequently asked",
          "questions",
          "data",
          "security",
          "export",
          "permissions",
          "role",
          "mobile",
          "conversation",
          "history",
        ],
      },
    ],
    []
  );

  const filteredSections = useMemo(() => {
    if (!searchQuery.trim()) return sections;
    const query = searchQuery.toLowerCase();
    return sections.filter(
      (section) =>
        section.label.toLowerCase().includes(query) ||
        section.keywords.some((k) => k.toLowerCase().includes(query))
    );
  }, [searchQuery, sections]);

  const highlightMatch = (text: string, query: string) => {
    if (!query.trim()) return text;
    const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const regex = new RegExp(`(${escaped})`, "gi");
    const parts = text.split(regex);
    return parts.map((part, i) =>
      regex.test(part) ? (
        <mark
          key={i}
          className="bg-[#582098]/20 text-[#582098] rounded px-0.5"
        >
          {part}
        </mark>
      ) : (
        part
      )
    );
  };

  const examplePrompts = [
    {
      category: "Portfolio KPIs",
      icon: TrendingUp,
      prompts: [
        "What is our current GMV?",
        "Show me the approval rate trend for the last 30 days",
        "Compare default rates across all regions",
      ],
    },
    {
      category: "Risk Analysis",
      icon: AlertTriangle,
      prompts: [
        "Give me the top 5 risky users",
        "Why is user_00497 flagged as high risk?",
        "What's the risk distribution in Casablanca?",
      ],
    },
    {
      category: "User Insights",
      icon: Users,
      prompts: [
        "Show me users with late payments this month",
        "Which users have exceeded their credit limit?",
        "Find users with more than 3 active plans",
      ],
    },
    {
      category: "Exports & Reports",
      icon: Download,
      prompts: [
        "Export the list of high-risk users",
        "Generate a monthly risk report",
        "Download payment performance data",
      ],
    },
  ];

  // Early return for loading state - must be after all hooks
  if (!user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#F8F8F8]">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-[#582098] border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F8F8F8]">
      <AppNavbar />

      <div className="flex">
        {/* Sidebar Navigation */}
        <aside className="sticky top-16 h-[calc(100vh-4rem)] w-64 border-r border-border bg-white p-4">
          <div className="mb-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#505050]" />
              <input
                type="text"
                placeholder="Search docs..."
                value={searchQuery}
                onChange={(e) => {
                  const next = e.target.value;
                  setSearchQuery(next);

                  // Auto-select first matching section if current section is filtered out
                  const q = next.toLowerCase();
                  if (q.trim()) {
                    const matches = sections.filter(
                      (s) =>
                        s.label.toLowerCase().includes(q) ||
                        s.keywords.some((k) => k.toLowerCase().includes(q))
                    );
                    if (
                      matches.length > 0 &&
                      !matches.find((s) => s.id === activeSection)
                    ) {
                      setActiveSection(matches[0].id);
                    }
                  }
                }}
                className="w-full rounded-lg border border-border bg-white py-2 pl-10 pr-4 text-sm text-[#303848] placeholder:text-[#505050] focus:border-[#582098] focus:outline-none focus:ring-1 focus:ring-[#582098]"
              />
            </div>
          </div>

          <nav className="space-y-1">
            {filteredSections.length > 0 ? (
              filteredSections.map((section) => (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-colors ${
                    activeSection === section.id
                      ? "bg-[#582098]/10 font-medium text-[#582098]"
                      : "text-[#505050] hover:bg-[#F8F8F8] hover:text-[#303848]"
                  }`}
                  type="button"
                >
                  <section.icon className="h-4 w-4" />
                  {highlightMatch(section.label, searchQuery)}
                </button>
              ))
            ) : (
              <div className="px-3 py-4 text-center text-sm text-[#505050]">
                No results found for "{searchQuery}"
              </div>
            )}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8">
          <div className="mx-auto max-w-4xl">
            {/* Getting Started */}
            {activeSection === "getting-started" && (
              <div>
                <div className="mb-8">
                  <div className="flex items-center gap-3 mb-4">
                    <img
                      src="/logo.png"
                      alt="BNPL Copilot"
                      width={52}
                      height={52}
                      className="h-13 w-13 object-contain"
                    />
                    <h1 className="text-3xl font-semibold text-[#303848]">
                      Getting Started with BNPL Copilot
                    </h1>
                  </div>
                  <p className="text-[#505050]">
                    Learn how to use the AI-powered assistant to analyze your BNPL
                    portfolio.
                  </p>
                </div>

                <div className="space-y-6">
                  <div className="rounded-xl border border-border bg-white p-6">
                    <h2 className="mb-4 text-xl font-semibold text-[#303848]">
                      What is BNPL Copilot?
                    </h2>
                    <p className="text-[#505050] leading-relaxed">
                      BNPL Copilot is an intelligent assistant powered by Gemini
                      AI and Local Pandas that helps you analyze your Buy Now Pay
                      Later portfolio data. Simply ask questions in plain
                      language and get instant KPIs, risk explanations, and
                      actionable recommendations.
                    </p>
                  </div>

                  <div className="rounded-xl border border-border bg-white p-6">
                    <h2 className="mb-4 text-xl font-semibold text-[#303848]">
                      Quick Start Guide
                    </h2>
                    <ol className="space-y-4">
                      {[
                        {
                          step: 1,
                          title: "Navigate to Copilot",
                          desc: "Click on 'Copilot' in the navigation bar to access the chat interface.",
                        },
                        {
                          step: 2,
                          title: "Start a new conversation",
                          desc: "Click 'New chat' to begin a fresh conversation with the AI assistant.",
                        },
                        {
                          step: 3,
                          title: "Ask your question",
                          desc: "Type your question about GMV, users, merchants, or risk in plain language.",
                        },
                        {
                          step: 4,
                          title: "Review the analysis",
                          desc: "View the AI's response and click 'View analysis' for detailed insights.",
                        },
                      ].map((item) => (
                        <li key={item.step} className="flex gap-4">
                          <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-[#582098] text-sm font-medium text-white">
                            {item.step}
                          </div>
                          <div>
                            <h3 className="font-medium text-[#303848]">
                              {item.title}
                            </h3>
                            <p className="text-sm text-[#505050]">{item.desc}</p>
                          </div>
                        </li>
                      ))}
                    </ol>
                  </div>

                  <div className="grid gap-4 sm:grid-cols-3">
                    {[
                      {
                        icon: Target,
                        title: "Accurate Insights",
                        desc: "Get precise KPIs and metrics from your portfolio data.",
                      },
                      {
                        icon: Zap,
                        title: "Instant Answers",
                        desc: "No more waiting for reports - get answers in seconds.",
                      },
                      {
                        icon: Shield,
                        title: "Secure Access",
                        desc: "Role-based permissions ensure data security.",
                      },
                    ].map((feature) => (
                      <div
                        key={feature.title}
                        className="rounded-xl border border-border bg-white p-5"
                      >
                        <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-[#582098]/10">
                          <feature.icon className="h-5 w-5 text-[#582098]" />
                        </div>
                        <h3 className="mb-1 font-medium text-[#303848]">
                          {feature.title}
                        </h3>
                        <p className="text-sm text-[#505050]">{feature.desc}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Asking Questions */}
            {activeSection === "asking-questions" && (
              <div>
                <div className="mb-8">
                  <h1 className="text-3xl font-semibold text-[#303848]">
                    Asking Questions
                  </h1>
                  <p className="mt-2 text-[#505050]">
                    Learn how to formulate effective questions for the best
                    results.
                  </p>
                </div>

                <div className="space-y-6">
                  <div className="rounded-xl border border-border bg-white p-6">
                    <h2 className="mb-4 text-xl font-semibold text-[#303848]">
                      Natural Language Queries
                    </h2>
                    <p className="mb-4 text-[#505050] leading-relaxed">
                      BNPL Copilot understands natural language, so you can ask
                      questions just like you would ask a colleague. No special
                      syntax or commands needed.
                    </p>
                    <div className="rounded-lg bg-[#F8F8F8] p-4">
                      <p className="mb-2 text-sm font-medium text-[#303848]">
                        Examples:
                      </p>
                      <ul className="space-y-2 text-sm text-[#505050]">
                        {[
                          "Who are the riskiest users in Rabat?",
                          "Show me GMV trends for the last quarter",
                          "Why is this user flagged as high risk?",
                        ].map((t) => (
                          <li key={t} className="flex items-center gap-2">
                            <ChevronRight className="h-4 w-4 text-[#582098]" />
                            "{t}"
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  <div className="rounded-xl border border-border bg-white p-6">
                    <h2 className="mb-4 text-xl font-semibold text-[#303848]">
                      Follow-up Questions
                    </h2>
                    <p className="mb-4 text-[#505050] leading-relaxed">
                      The Copilot maintains context within a conversation, so you
                      can ask follow-up questions without repeating information.
                    </p>
                    <div className="space-y-3">
                      <div className="rounded-lg bg-[#582098] px-4 py-2 text-sm text-white">
                        "Show me high-risk users"
                      </div>
                      <div className="ml-8 rounded-lg border border-border bg-white px-4 py-2 text-sm text-[#303848]">
                        Here are the top 5 high-risk users...
                      </div>
                      <div className="rounded-lg bg-[#582098] px-4 py-2 text-sm text-white">
                        "Why is the first one risky?"
                      </div>
                      <div className="ml-8 rounded-lg border border-border bg-white px-4 py-2 text-sm text-[#303848]">
                        User_00497 is risky due to low income and high debt-to-income
                        ratio...
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Understanding Analytics */}
            {activeSection === "understanding-analytics" && (
              <div>
                <div className="mb-8">
                  <h1 className="text-3xl font-semibold text-[#303848]">
                    Understanding Analytics
                  </h1>
                  <p className="mt-2 text-[#505050]">
                    Learn how to interpret the analytics panel and visualizations.
                  </p>
                </div>

                <div className="space-y-6">
                  <div className="rounded-xl border border-border bg-white p-6">
                    <h2 className="mb-4 text-xl font-semibold text-[#303848]">
                      The Analytics Panel
                    </h2>
                    <p className="mb-4 text-[#505050] leading-relaxed">
                      The analytics panel on the right side of the Copilot interface
                      provides real-time visualizations related to your current
                      conversation.
                    </p>
                    <div className="grid gap-4 sm:grid-cols-3">
                      {[
                        { tab: "Overview", desc: "Key metrics and KPI cards for quick insights" },
                        { tab: "Charts", desc: "Visual representations of trends and distributions" },
                        { tab: "Details", desc: "Detailed breakdowns and recommendations" },
                      ].map((item) => (
                        <div key={item.tab} className="rounded-lg bg-[#F8F8F8] p-4">
                          <h3 className="mb-1 font-medium text-[#582098]">{item.tab}</h3>
                          <p className="text-sm text-[#505050]">{item.desc}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="rounded-xl border border-border bg-white p-6">
                    <h2 className="mb-4 text-xl font-semibold text-[#303848]">
                      Key Metrics Explained
                    </h2>
                    <div className="space-y-4">
                      {[
                        { metric: "Late Rate", desc: "Percentage of users with overdue payments", icon: TrendingUp },
                        { metric: "Risk Score", desc: "Overall risk assessment based on multiple factors", icon: AlertTriangle },
                        { metric: "Scored Users", desc: "Number of users who have been risk-assessed", icon: Users },
                      ].map((item) => (
                        <div key={item.metric} className="flex items-start gap-4">
                          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-[#582098]/10">
                            <item.icon className="h-5 w-5 text-[#582098]" />
                          </div>
                          <div>
                            <h3 className="font-medium text-[#303848]">{item.metric}</h3>
                            <p className="text-sm text-[#505050]">{item.desc}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Example Prompts */}
            {activeSection === "example-prompts" && (
              <div>
                <div className="mb-8">
                  <h1 className="text-3xl font-semibold text-[#303848]">
                    Example Prompts
                  </h1>
                  <p className="mt-2 text-[#505050]">
                    Try these example prompts to explore the Copilot's capabilities.
                  </p>
                </div>

                <div className="space-y-6">
                  {examplePrompts.map((category) => (
                    <div
                      key={category.category}
                      className="rounded-xl border border-border bg-white p-6"
                    >
                      <div className="mb-4 flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#582098]/10">
                          <category.icon className="h-5 w-5 text-[#582098]" />
                        </div>
                        <h2 className="text-lg font-semibold text-[#303848]">
                          {category.category}
                        </h2>
                      </div>

                      <div className="space-y-2">
                        {category.prompts.map((prompt, index) => (
                          <div
                            key={index}
                            className="flex items-center justify-between rounded-lg bg-[#F8F8F8] px-4 py-3"
                          >
                            <span className="text-sm text-[#303848]">{prompt}</span>
                            <button
                              className="text-xs font-medium text-[#582098] hover:underline"
                              type="button"
                            >
                              Try it
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tips & Tricks */}
            {activeSection === "tips-tricks" && (
              <div>
                <div className="mb-8">
                  <h1 className="text-3xl font-semibold text-[#303848]">
                    Tips & Tricks
                  </h1>
                  <p className="mt-2 text-[#505050]">
                    Get the most out of BNPL Copilot with these helpful tips.
                  </p>
                </div>

                <div className="space-y-4">
                  {[
                    {
                      title: "Be Specific",
                      desc: "Instead of 'show users', try 'show high-risk users in Casablanca with late payments'.",
                      color: "#582098",
                    },
                    {
                      title: "Use Time Frames",
                      desc: "Specify time periods like 'last 30 days', 'this quarter', or 'since January'.",
                      color: "#608818",
                    },
                    {
                      title: "Ask for Explanations",
                      desc: "Follow up with 'why' questions to understand the reasoning behind insights.",
                      color: "#f59e0b",
                    },
                    {
                      title: "Request Comparisons",
                      desc: "Compare metrics across regions, time periods, or user segments.",
                      color: "#582098",
                    },
                    {
                      title: "Use the Analytics Panel",
                      desc: "Toggle the analytics panel for visual representations of your queries.",
                      color: "#608818",
                    },
                    {
                      title: "Save Important Chats",
                      desc: "Your chat history is saved, so you can revisit important conversations.",
                      color: "#f59e0b",
                    },
                  ].map((tip, index) => (
                    <div
                      key={index}
                      className="flex items-start gap-4 rounded-xl border border-border bg-white p-5"
                    >
                      <div
                        className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full text-sm font-medium text-white"
                        style={{ backgroundColor: tip.color }}
                      >
                        {index + 1}
                      </div>
                      <div>
                        <h3 className="font-medium text-[#303848]">{tip.title}</h3>
                        <p className="text-sm text-[#505050]">{tip.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* FAQ */}
            {activeSection === "faq" && (
              <div>
                <div className="mb-8">
                  <h1 className="text-3xl font-semibold text-[#303848]">
                    Frequently Asked Questions
                  </h1>
                  <p className="mt-2 text-[#505050]">
                    Common questions about using BNPL Copilot.
                  </p>
                </div>

                <div className="space-y-4">
                  {[
                    {
                      q: "How accurate are the AI responses?",
                      a: "The Copilot uses your actual portfolio data to generate responses. All metrics and KPIs are calculated in real-time from your database.",
                    },
                    {
                      q: "Can I export the analysis results?",
                      a: "Yes, you can ask the Copilot to export data in various formats. Simply say 'export this as CSV' or 'generate a PDF report'.",
                    },
                    {
                      q: "Is my data secure?",
                      a: "Absolutely. All data is processed securely with role-based access controls. Only users with appropriate permissions can access sensitive information.",
                    },
                    {
                      q: "What if the AI doesn't understand my question?",
                      a: "Try rephrasing your question or being more specific. You can also check the Example Prompts section for guidance on how to phrase queries.",
                    },
                    {
                      q: "How often is the data updated?",
                      a: "The Copilot accesses real-time data from your connected systems. Updates depend on your data pipeline configuration.",
                    },
                  ].map((faq, index) => (
                    <div
                      key={index}
                      className="rounded-xl border border-border bg-white p-6"
                    >
                      <h3 className="mb-2 font-medium text-[#303848]">{faq.q}</h3>
                      <p className="text-sm text-[#505050] leading-relaxed">{faq.a}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
