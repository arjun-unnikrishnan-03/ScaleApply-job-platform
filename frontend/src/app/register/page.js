"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import api from "@/lib/api";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("candidate");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await api.post("/api/auth/register", { email, password, role });
      router.push("/login");
    } catch (err) {
      const issue = err.response?.data?.details?.[0]?.message;
      setError(issue || err.response?.data?.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[80vh]">
      <div className="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md border border-gray-100">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Create Account</h1>
          <p className="text-gray-500 text-sm">Join JobSync to find or post jobs</p>
        </div>

        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm mb-6 text-center font-medium">
            {error}
          </div>
        )}

        <form onSubmit={handleRegister} className="space-y-5">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1.5">Email Address</label>
            <input
              type="email"
              required
              autoComplete="email"
              suppressHydrationWarning
              className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1.5">Password (min 8 characters)</label>
            <input
              type="password"
              required
              minLength={8}
              autoComplete="new-password"
              suppressHydrationWarning
              className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1.5">I am a...</label>
            <div className="grid grid-cols-2 gap-4">
              {["candidate", "recruiter"].map((option) => (
                <label
                  key={option}
                  className={`cursor-pointer border rounded-xl py-3 text-center text-sm font-medium transition-all ${role === option ? "border-blue-600 bg-blue-50 text-blue-700" : "border-gray-200 text-gray-600 hover:bg-gray-50"}`}
                >
                  <input
                    type="radio"
                    name="role"
                    value={option}
                    checked={role === option}
                    suppressHydrationWarning
                    onChange={(e) => setRole(e.target.value)}
                    className="hidden"
                  />
                  {option.charAt(0).toUpperCase() + option.slice(1)}
                </label>
              ))}
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            suppressHydrationWarning
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition-colors shadow-md shadow-blue-500/20 disabled:opacity-70 disabled:cursor-not-allowed mt-4"
          >
            {loading ? "Creating account..." : "Sign Up"}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-gray-600 font-medium">
          Already have an account?{" "}
          <Link href="/login" className="text-blue-600 hover:text-blue-700 font-semibold transition-colors">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}
