"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import { useRouter } from "next/navigation";
import { isAuthenticated, getRole } from "@/utils/auth";
import { Briefcase, Users, FileText, ChevronDown, ChevronUp, UserCircle } from "lucide-react";

export default function Dashboard() {
  const [jobs, setJobs] = useState([]);
  const [expandedJob, setExpandedJob] = useState(null);
  const [applications, setApplications] = useState({});
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated() || getRole() !== "recruiter") {
      router.push("/login");
      return;
    }

    const fetchMyJobs = async () => {
      try {
        const token = localStorage.getItem("token");
        const response = await axios.get(
          `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000"}/api/jobs/me`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setJobs(response.data);
      } catch (err) {
        console.error("Failed to fetch jobs", err);
      } finally {
        setLoading(false);
      }
    };

    fetchMyJobs();
  }, [router]);

  const loadApplications = async (jobId) => {
    if (expandedJob === jobId) {
      setExpandedJob(null);
      return;
    }

    setExpandedJob(jobId);
    
    // Only fetch if we haven't already
    if (!applications[jobId]) {
      try {
        const token = localStorage.getItem("token");
        const response = await axios.get(
          `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000"}/api/applications/job/${jobId}`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setApplications(prev => ({ ...prev, [jobId]: response.data }));
      } catch (err) {
        console.error("Failed to fetch applications", err);
      }
    }
  };

  if (loading) {
    return <div className="text-center py-20 text-gray-500 font-medium">Loading Dashboard...</div>;
  }

  return (
    <div className="max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Recruiter Dashboard</h1>
          <p className="text-gray-500 mt-2">Manage your job postings and view AI-matched candidates.</p>
        </div>
        <button 
          onClick={() => router.push("/post-job")}
          className="bg-gray-900 hover:bg-gray-800 text-white px-5 py-2.5 rounded-lg font-medium transition-colors flex items-center gap-2 text-sm"
        >
          <Briefcase size={16} />
          Post New Job
        </button>
      </div>

      {jobs.length === 0 ? (
        <div className="text-center py-20 bg-white rounded-2xl border border-gray-100 shadow-sm">
          <Briefcase className="mx-auto h-12 w-12 text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900">No jobs posted yet</h3>
          <p className="text-gray-500 mt-1 mb-6">Create your first job listing to attract candidates.</p>
          <button 
            onClick={() => router.push("/post-job")}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2.5 rounded-lg font-medium transition-colors"
          >
            Create Job Listing
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {jobs.map((job) => (
            <div key={job._id} className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
              <div 
                onClick={() => loadApplications(job._id)}
                className="p-6 cursor-pointer hover:bg-gray-50 transition-colors flex items-center justify-between"
              >
                <div>
                  <h2 className="text-xl font-bold text-gray-900 mb-1">{job.title}</h2>
                  <p className="text-gray-500 text-sm line-clamp-1 max-w-2xl">{job.description}</p>
                </div>
                <div className="flex items-center gap-4 text-gray-400">
                  <div className="flex items-center gap-1.5 bg-gray-100 px-3 py-1 rounded-lg text-sm font-medium text-gray-700">
                    <Users size={16} />
                    View Matches
                  </div>
                  {expandedJob === job._id ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                </div>
              </div>

              {expandedJob === job._id && (
                <div className="border-t border-gray-100 bg-gray-50 p-6">
                  <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-4">
                    Candidates by AI Match Score
                  </h3>
                  
                  {!applications[job._id] ? (
                    <div className="text-sm text-gray-500 animate-pulse">Loading matches...</div>
                  ) : applications[job._id].length === 0 ? (
                    <div className="text-sm text-gray-500 italic">No candidates have applied yet.</div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {applications[job._id].map(app => (
                        <div key={app._id} className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center gap-2">
                              <UserCircle className="text-gray-400" size={24} />
                              <span className="font-semibold text-gray-900 text-sm">
                                {app.userId?.email || "Unknown User"}
                              </span>
                            </div>
                            <div className={`px-2.5 py-1 rounded-md text-xs font-bold ${
                              app.score >= 80 ? 'bg-green-100 text-green-800' :
                              app.score >= 50 ? 'bg-yellow-100 text-yellow-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              Score: {app.score || 0}/100
                            </div>
                          </div>
                          
                          <div className="bg-gray-50 p-3 rounded-lg border border-gray-100 text-xs text-gray-600 leading-relaxed max-h-32 overflow-y-auto mb-3">
                            <span className="font-bold text-gray-700 block mb-1">AI Explanation:</span>
                            {app.explanation || "No explanation available."}
                          </div>

                          <a 
                            href={app.resumeUrl} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 text-xs font-medium text-blue-600 hover:text-blue-800 transition-colors"
                          >
                            <FileText size={14} />
                            View Resume PDF
                          </a>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
