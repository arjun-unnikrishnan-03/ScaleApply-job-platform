"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { isAuthenticated, getRole } from "@/utils/auth";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated()) {
      if (getRole() === "recruiter") {
        router.push("/post-job");
      } else {
        router.push("/jobs");
      }
    } else {
      router.push("/login");
    }
  }, [router]);

  return null; // Empty render while redirecting
}
