import { Routes, Route, Navigate } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import DocsPage from "./pages/DocsPage";
import CopilotPage from "./pages/CopilotPage";
import FeedbackPage from "./pages/FeedbackPage";
import RequireAuth from "./routes/RequireAuth";
import RequireRole from "./routes/RequireRole";

function App() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />

      {/* Protected */}
      <Route
        path="/dashboard"
        element={
          <RequireAuth>
            <DashboardPage />
          </RequireAuth>
        }
      />
      {/* Admin, Analyst, and Developer only: Documentation */}
      <Route
        path="/docs"
        element={
          <RequireRole allowedRoles={["admin", "analyst", "developer"]}>
            <DocsPage />
          </RequireRole>
        }
      />
      {/* Admin and Analyst only: Copilot Chat */}
      <Route
        path="/copilot"
        element={
          <RequireRole allowedRoles={["admin", "analyst"]}>
            <CopilotPage />
          </RequireRole>
        }
      />
      {/* Admin and Developer only: Feedback Dashboard */}
      <Route
        path="/feedback"
        element={
          <RequireRole allowedRoles={["admin", "developer"]}>
            <FeedbackPage />
          </RequireRole>
        }
      />

      {/* Optional placeholder */}
      <Route path="/request-access" element={<Navigate to="/login" replace />} />

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
