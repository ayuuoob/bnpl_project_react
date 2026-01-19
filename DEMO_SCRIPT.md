# 🎙️ BNPL Intelligent Analytics - Demo Script

## 1. The Executive Dashboard (1 min)

**Action**: Login as `ceo@bnpl.com` / `ceo123`.
**Screen**: Landing on the Dashboard.

> "We start here at the Executive Dashboard. This isn't just a mock-up; it's connected to our live 'Gold Layer' data."

*   **Point out KPIs**: "You can see our real-time GMV (Gross Merchandise Value), Approval Rates, and Default Rates updated instantly."
*   **Show Charts**: "On the right, we have the Risk Distribution by City. We can instantly see that Casablanca has a higher volume but steady risk profile."
*   **Transition**: "But dashboards only answer *known* questions. What if I have a question the dashboard wasn't built for?"

---

## 2. The AI Copilot - Educational Capability (1.5 min)

**Action**: Click "Copilot" in the sidebar.
**Screen**: Chat Interface.

> "This is the **AI Copilot**, powered by a multi-agent system (LangGraph + Gemini). It's not just a database query tool; it understands business concepts."

**Action**: Type: `What is the difference between Risk and Trust score?`

> "First, let's ask it a conceptual question. Many junior analysts struggle with these definitions."

*(Wait for response)*

> "Notice the response. It doesn't give me a database error. It explains clearly that Risk is about *late payment probability* (Bad) and Trust is about *reliability* (Good). It's acting as a mentor, not just a machine."

---

## 3. The AI Copilot - Data & Memory (2 min)

> "Now, let's do some actual analysis."

**Action**: Type: `Show me high risk users in Rabat`

> "I'm asking for data using natural language. Behind the scenes, the **Planner** works out my intent (Risk Analysis), extracts the entity ('Rabat'), and the **Executor** filters thousands of rows in milliseconds."

*(Show the table/chart that appears)*

> "It gives me a list of users. But here is the magic: **Memory**."

**Action**: Type: `Which of them have a risk score above 80%?`

> "I didn't say 'users in Rabat' again. I said 'them'. The agent understands the context of our conversation and refines the previous detailed list."

*(Show the refined list)*

---

## 4. Architecture & Security (1 min)

> "Finally, enterprise security is built-in."

**Action**: Log out. Log in as `viewer@bnpl.com` / `viewer123`.

> "I'm now logging in as a 'Viewer' - maybe an external auditor or junior staff."

**Action**: Try to click "Copilot" (It should be hidden or locked).

> "Notice that the Copilot and detailed Logs are completely inaccessible. The system strictly enforces Role-Based Access Control (RBAC), ensuring sensitive AI tools are only for authorized personnel."

---

## 🏁 Conclusion

> "To summarize: We've built a system that is **Descriptive** (Dashboard), **Educational** (Concept Explainer), and **Diagnostic** (Deep Dive Data Search), all wrapped in a secure, easy-to-use interface. Thank you!"
