import { Navigate, useLocation } from "react-router-dom";
import { getCurrentUser, type UserRole } from "../lib/auth";

interface RequireRoleProps {
    children: React.ReactNode;
    allowedRoles: UserRole[];
}

export default function RequireRole({ children, allowedRoles }: RequireRoleProps) {
    const location = useLocation();
    const user = getCurrentUser();

    // Not logged in -> redirect to login
    if (!user) {
        return <Navigate to="/login" replace state={{ from: location.pathname }} />;
    }

    // Logged in but wrong role -> redirect to dashboard with message
    if (!allowedRoles.includes(user.role)) {
        return (
            <div className="flex flex-col items-center justify-center h-screen bg-[#F8F8F8]">
                <div className="bg-white p-8 rounded-xl border border-border shadow-sm text-center max-w-md">
                    <div className="text-5xl mb-4">🔒</div>
                    <h2 className="text-xl font-bold text-[#303848] mb-2">Access Restricted</h2>
                    <p className="text-[#505050] mb-4">
                        This page is only available to <strong>{allowedRoles.join(", ")}</strong> users.
                    </p>
                    <p className="text-sm text-[#505050] mb-6">
                        You are logged in as: <span className="font-medium capitalize">{user.role}</span>
                    </p>
                    <a
                        href="/dashboard"
                        className="inline-block px-6 py-2 bg-[#582098] text-white rounded-lg hover:bg-[#582098]/90 transition-colors"
                    >
                        Go to Dashboard
                    </a>
                </div>
            </div>
        );
    }

    return <>{children}</>;
}
