"use client";

import Link from "next/link";
import { Briefcase, UserCircle, LogOut } from "lucide-react";
import { useEffect, useState } from "react";
import { isAuthenticated, getRole, logout } from "@/utils/auth";
import { useRouter } from "next/navigation";
import { io } from "socket.io-client";
import toast from "react-hot-toast";

export default function Navbar() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userRole, setUserRole] = useState(null);

  useEffect(() => {
    setIsLoggedIn(isAuthenticated());
    const role = getRole();
    setUserRole(role);

    // Setup WebSocket exclusively for recruiters to get live application drops
    if (role === "recruiter") {
      const socket = io(process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000");

      socket.on("new_application", (data) => {
        toast.success(`New application received for Job ID: ${data.jobId.slice(-4)}!`, {
          duration: 5000,
          icon: '🎉',
        });
      });

      return () => {
        socket.disconnect();
      };
    }
  }, []);

  return (
    <nav className="bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between sticky top-0 z-50 shadow-sm">
      <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
        <div className="bg-blue-600 text-white p-2 rounded-lg">
          <Briefcase size={20} />
        </div>
        <span className="font-bold text-xl tracking-tight text-gray-900">JobSync</span>
      </Link>
      <div className="flex items-center gap-4">
        {!isLoggedIn ? (
          <>
            <Link 
              href="/login" 
              className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
            >
              Sign In
            </Link>
            <Link 
              href="/register" 
              className="text-sm font-medium bg-gray-900 text-white px-4 py-2 rounded-lg hover:bg-gray-800 transition-colors"
            >
              Sign Up
            </Link>
          </>
        ) : (
          <>
            {userRole === "recruiter" && (
              <Link 
                href="/dashboard" 
                className="text-sm font-semibold text-gray-700 hover:text-blue-600 transition-colors mr-4"
              >
                Dashboard
              </Link>
            )}
            {userRole === "candidate" && (
              <Link 
                href="/jobs" 
                className="text-sm font-semibold text-gray-700 hover:text-blue-600 transition-colors mr-4"
              >
                Find Jobs
              </Link>
            )}
            <span className="bg-blue-50 text-blue-700 text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider">
              {userRole || "User"}
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
