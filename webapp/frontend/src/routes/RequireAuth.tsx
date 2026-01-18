import { Navigate, useLocation } from "react-router-dom";
import { getCurrentUser } from "../lib/auth";

export default function RequireAuth({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const user = getCurrentUser();

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <>{children}</>;
}
