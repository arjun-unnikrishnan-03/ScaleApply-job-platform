"use client";

import { useState, useEffect, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { UploadCloud, CheckCircle, ArrowLeft } from "lucide-react";
import toast from "react-hot-toast";
import api from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { getSocket } from "@/lib/socket";

export default function ApplyPage({ params }) {
  const unwrappedParams = use(params);
  const jobId = unwrappedParams.id;

  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [applicationId, setApplicationId] = useState(null);
  const [scoring, setScoring] = useState(true);
  const [matchData, setMatchData] = useState(null);
  const router = useRouter();
  const { ready, isAuthenticated, role } = useAuth();

  useEffect(() => {
    if (!ready) return;
    if (!isAuthenticated) router.replace("/login");
    else if (role !== "candidate") router.replace("/dashboard");
  }, [ready, isAuthenticated, role, router]);

  useEffect(() => {
    if (!submitted || !applicationId) return;
    const socket = getSocket();
    if (!socket) return;
    const handler = (data) => {
      if (String(data.applicationId) !== String(applicationId)) return;
      setMatchData({ score: data.score, explanation: data.explanation });
      setScoring(false);
    };
    socket.on("application:scored", handler);
    return () => socket.off("application:scored", handler);
  }, [submitted, applicationId]);

  const handleFileChange = (e) => {
    if (e.target.files?.[0]) setFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a resume file.");
      return;
    }
    setLoading(true);
    setError("");

    const formData = new FormData();
    formData.append("resume", file);
    try {
      const { data } = await api.post(`/api/applications/${jobId}`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setApplicationId(data.id);
      setSubmitted(true);
      toast.success("Application submitted! Scoring your resume...");
    } catch (err) {
      setError(err.response?.data?.message || "Failed to submit application");
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center max-w-lg mx-auto">
        <div className="w-20 h-20 bg-green-50 rounded-full flex items-center justify-center mb-6">
          <CheckCircle className="text-green-500 w-10 h-10" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Application Sent!</h1>
        <p className="text-gray-500 mb-8">The recruiter has been notified of your application.</p>

        {scoring && !matchData && (
          <div className="bg-blue-50 border border-blue-100 rounded-xl p-6 mb-8 w-full">
            <div className="flex items-center justify-center gap-3">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
              <p className="text-blue-700 text-sm font-medium">AI is scoring your resume...</p>
            </div>
          </div>
        )}

        {matchData && matchData.score !== null && (
          <div className="bg-green-50 border border-green-200 rounded-xl p-6 mb-8 text-left w-full shadow-sm">
            <h3 className="text-lg font-bold text-green-800 mb-2">AI Match Score: {matchData.score}/100</h3>
            <p className="text-green-700 text-sm leading-relaxed">{matchData.explanation || "No explanation provided."}</p>
          </div>
        )}

        {matchData && matchData.score === null && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6 mb-8 text-left w-full shadow-sm">
            <h3 className="text-lg font-bold text-yellow-800 mb-2">Match Score Unavailable</h3>
            <p className="text-yellow-700 text-sm leading-relaxed">{matchData.explanation}</p>
          </div>
        )}

        <Link
          href="/jobs"
          className="bg-gray-900 hover:bg-gray-800 text-white px-6 py-3 rounded-lg font-medium transition-colors w-full"
        >
          Back to Jobs
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <Link href="/jobs" className="inline-flex items-center text-sm font-medium text-gray-500 hover:text-gray-900 mb-8 transition-colors">
        <ArrowLeft size={16} className="mr-2" />
        Back to Jobs
      </Link>

      <div className="bg-white p-8 sm:p-10 rounded-2xl shadow-sm border border-gray-100">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Submit Your Application</h1>
        <p className="text-gray-500 text-sm mb-8">Upload your resume to apply for this position.</p>

        {error && (
          <div className="bg-red-50 text-red-600 p-4 rounded-xl text-sm mb-6 font-medium">{error}</div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="mb-8">
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              Resume (PDF, DOC, DOCX)
            </label>

            <div className="relative border-2 border-dashed border-gray-200 rounded-xl p-8 hover:bg-gray-50 transition-colors group text-center cursor-pointer">
              <input
                type="file"
                accept=".pdf,.doc,.docx"
                onChange={handleFileChange}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <UploadCloud className="mx-auto h-10 w-10 text-gray-400 group-hover:text-blue-500 transition-colors mb-3" />
              <p className="text-sm text-gray-600 font-medium">
                {file ? file.name : "Click to upload or drag and drop"}
              </p>
              <p className="text-xs text-gray-400 mt-1">Max file size: 5MB</p>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !file}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3.5 rounded-xl transition-all shadow-md shadow-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none"
          >
            {loading ? "Submitting securely..." : "Submit Application"}
          </button>
        </form>
      </div>
    </div>
  );
}
