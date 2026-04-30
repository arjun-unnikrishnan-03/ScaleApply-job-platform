"use client";

import Link from "next/link";
import { Briefcase, LogOut } from "lucide-react";
import { useEffect } from "react";
import toast from "react-hot-toast";
import { useAuth } from "@/contexts/AuthContext";
import { getSocket } from "@/lib/socket";

export default function Navbar() {
  const { isAuthenticated, role, logout, ready } = useAuth();

  useEffect(() => {
    if (!ready || !isAuthenticated) return;
    const socket = getSocket();
    if (!socket) return;

    if (role === "recruiter") {
      const handler = (data) => {
        if (data.type === "scored") return;
        toast.success(`New application for "${data.jobTitle}"`, { duration: 5000, icon: "🎉" });
      };
      socket.on("application:new", handler);
      return () => socket.off("application:new", handler);
    }

    if (role === "candidate") {
      const handler = (data) => {
        if (data.score === null) return;
        toast.success(`AI scored your application: ${data.score}/100`, { duration: 6000 });
      };
      socket.on("application:scored", handler);
      return () => socket.off("application:scored", handler);
    }
  }, [ready, isAuthenticated, role]);

  return (
    <nav className="bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between sticky top-0 z-50 shadow-sm">
      <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
        <div className="bg-blue-600 text-white p-2 rounded-lg">
          <Briefcase size={20} />
        </div>
        <span className="font-bold text-xl tracking-tight text-gray-900">JobSync</span>
      </Link>
      <div className="flex items-center gap-4">
        {!isAuthenticated ? (
          <>
            <Link href="/login" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">
              Sign In
            </Link>
            <Link href="/register" className="text-sm font-medium bg-gray-900 text-white px-4 py-2 rounded-lg hover:bg-gray-800 transition-colors">
              Sign Up
            </Link>
          </>
        ) : (
          <>
            {role === "recruiter" && (
              <Link href="/dashboard" className="text-sm font-semibold text-gray-700 hover:text-blue-600 transition-colors mr-4">
                Dashboard
              </Link>
            )}
            {role === "candidate" && (
              <Link href="/jobs" className="text-sm font-semibold text-gray-700 hover:text-blue-600 transition-colors mr-4">
                Find Jobs
              </Link>
            )}
            <span className="bg-blue-50 text-blue-700 text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider">
              {role || "User"}
            </span>
            <button
              onClick={logout}
              className="text-sm font-medium text-red-600 hover:bg-red-50 px-3 py-2 rounded-lg transition-colors flex items-center gap-2"
            >
              <LogOut size={16} />
              Logout
            </button>
          </>
        )}
      </div>
    </nav>
  );
}
