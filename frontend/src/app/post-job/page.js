"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Briefcase, CheckCircle } from "lucide-react";
import api from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";

export default function PostJobPage() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const router = useRouter();
  const { ready, isAuthenticated, role } = useAuth();

  useEffect(() => {
    if (!ready) return;
    if (!isAuthenticated) router.replace("/login");
    else if (role !== "recruiter") router.replace("/jobs");
  }, [ready, isAuthenticated, role, router]);

  const handlePostJob = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await api.post("/api/jobs", { title, description });
      setSuccess(true);
    } catch (err) {
      const issue = err.response?.data?.details?.[0]?.message;
      setError(issue || err.response?.data?.message || "Failed to post job");
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center max-w-lg mx-auto">
        <div className="w-20 h-20 bg-green-50 rounded-full flex items-center justify-center mb-6">
          <CheckCircle className="text-green-500 w-10 h-10" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Job Posted!</h1>
        <p className="text-gray-500 mb-8">Your job listing is now live and visible to candidates.</p>
        <button
          onClick={() => { setSuccess(false); setTitle(""); setDescription(""); }}
          className="bg-gray-900 hover:bg-gray-800 text-white px-6 py-3 rounded-lg font-medium transition-colors w-full"
        >
          Post Another Job
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="bg-white p-8 sm:p-10 rounded-2xl shadow-sm border border-gray-100">
        <div className="flex items-center gap-3 mb-8">
          <div className="bg-blue-50 text-blue-600 p-3 rounded-xl">
            <Briefcase size={24} />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Post a New Job</h1>
            <p className="text-gray-500 text-sm">Create a listing to find your next great candidate.</p>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 text-red-600 p-4 rounded-xl text-sm mb-6 font-medium">{error}</div>
        )}

        <form onSubmit={handlePostJob} className="space-y-6">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Job Title</label>
            <input
              type="text"
              required
              maxLength={200}
              className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-gray-50 focus:bg-white"
              placeholder="e.g. Senior Frontend Engineer"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Job Description</label>
            <textarea
              required
              rows={6}
              maxLength={10000}
              className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-gray-50 focus:bg-white"
              placeholder="Describe the role, responsibilities, and requirements..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3.5 rounded-xl transition-all shadow-md shadow-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Publishing Job..." : "Publish Job Listing"}
          </button>
        </form>
      </div>
    </div>
  );
}
