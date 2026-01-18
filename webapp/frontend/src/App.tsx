import { Routes, Route, Navigate } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import DocsPage from "./pages/DocsPage";
import CopilotPage from "./pages/CopilotPage";
import RequireAuth from "./routes/RequireAuth";

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
      <Route
        path="/docs"
        element={
          <RequireAuth>
            <DocsPage />
          </RequireAuth>
        }
      />
      <Route
        path="/copilot"
        element={
          <RequireAuth>
            <CopilotPage />
          </RequireAuth>
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
