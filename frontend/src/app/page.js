"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

export default function Home() {
  const router = useRouter();
  const { ready, isAuthenticated, role } = useAuth();

  useEffect(() => {
    if (!ready) return;
    if (!isAuthenticated) router.replace("/login");
    else router.replace(role === "recruiter" ? "/dashboard" : "/jobs");
  }, [ready, isAuthenticated, role, router]);

  return null;
}
