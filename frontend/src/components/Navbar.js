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
    <nav className="sticky top-0 z-50 w-full border-b border-gray-200/50 bg-white/75 backdrop-blur-md shadow-[0_2px_15px_-3px_rgba(0,0,0,0.05)] transition-all duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3.5 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5 hover:opacity-90 active:scale-95 transition-all">
          <div className="bg-gradient-to-tr from-blue-600 to-indigo-600 text-white p-2.5 rounded-xl shadow-md shadow-blue-500/10">
            <Briefcase size={18} />
          </div>
          <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">JobSync</span>
        </Link>
        <div className="flex items-center gap-4">
          {!isAuthenticated ? (
            <>
              <Link href="/login" className="text-sm font-semibold text-gray-600 hover:text-gray-900 transition-colors py-2 px-3 rounded-lg hover:bg-gray-50">
                Sign In
              </Link>
              <Link href="/register" className="text-sm font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-4.5 py-2.5 rounded-xl hover:from-blue-700 hover:to-indigo-700 hover:shadow-lg hover:shadow-blue-500/10 transition-all duration-300 active:scale-95">
                Get Started
              </Link>
            </>
          ) : (
            <>
              {role === "recruiter" && (
                <Link href="/dashboard" className="text-sm font-semibold text-gray-700 hover:text-blue-600 transition-colors py-2 px-3 rounded-lg hover:bg-blue-50/50">
                  Dashboard
                </Link>
              )}
              {role === "candidate" && (
                <>
                  <Link href="/jobs" className="text-sm font-semibold text-gray-700 hover:text-blue-600 transition-colors py-2 px-3 rounded-lg hover:bg-blue-50/50">
                    Find Jobs
                  </Link>
                  <Link href="/profile" className="text-sm font-semibold text-gray-700 hover:text-blue-600 transition-colors py-2 px-3 rounded-lg hover:bg-blue-50/50">
                    Profile
                  </Link>
                </>
              )}
              <span className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-100 text-blue-700 text-[10px] font-extrabold px-3 py-1 rounded-full uppercase tracking-wider shadow-sm">
                {role || "User"}
              </span>
              <button
                onClick={logout}
                className="text-sm font-semibold text-red-600 hover:bg-red-50 hover:text-red-700 px-3 py-2 rounded-xl transition-all flex items-center gap-1.5 active:scale-95"
              >
                <LogOut size={15} />
                Logout
              </button>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
