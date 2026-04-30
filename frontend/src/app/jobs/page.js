"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Briefcase, Building2, Clock, X, ChevronRight } from "lucide-react";
import { isAuthenticated } from "@/utils/auth";

export default function JobsPage() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedJob, setSelectedJob] = useState(null); // State for JD Modal
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }

    const fetchJobs = async () => {
      try {
        const response = await axios.get(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000"}/api/jobs`);
        setJobs(response.data);
      } catch (error) {
        console.error("Failed to fetch jobs:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchJobs();
  }, [router]);

  // JD Parser: Converts raw text into structured bullet points
  const parseJobDescription = (text) => {
    if (!text) return { responsibilities: [], skills: [] };
    
    // Split by newlines or periods followed by a space
    const segments = text.split(/\n|\. /)
      .map(s => s.trim().replace(/^\./, '').trim())
      .filter(s => s.length > 10); // Ignore tiny fragments
      
    // If not enough segments, just return it as one big responsibility
    if (segments.length <= 2) {
      return { responsibilities: segments, skills: [] };
    }

    // Heuristically split the segments in half for structure
    const splitIndex = Math.ceil(segments.length / 2);
    return {
      responsibilities: segments.slice(0, splitIndex),
      skills: segments.slice(splitIndex)
    };
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8 relative">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Explore Opportunities</h1>
        <p className="text-gray-500 mt-2">Find and apply to the best jobs curated for you.</p>
      </div>

      {jobs.length === 0 ? (
        <div className="text-center py-20 bg-white rounded-2xl border border-gray-100 shadow-sm">
          <Briefcase className="mx-auto h-12 w-12 text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900">No jobs found</h3>
          <p className="text-gray-500">Check back later for new opportunities.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {jobs.map((job) => (
            <div 
              key={job._id} 
              className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 flex flex-col h-full"
            >
              <div className="flex-1">
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center shrink-0">
                    <Building2 size={24} />
                  </div>
                  <span className="bg-green-50 text-green-700 text-xs font-semibold px-2.5 py-1 rounded-full whitespace-nowrap">
                    Active
                  </span>
                </div>
                
                <h2 className="text-xl font-bold text-gray-900 mb-2 line-clamp-1">{job.title}</h2>
                
                {/* Truncated Description */}
                <p className="text-gray-500 text-sm leading-relaxed mb-1">
                  {job.description?.slice(0, 120)}
                  {job.description?.length > 120 ? "..." : ""}
                </p>
                
                {/* Read More Button */}
                {job.description?.length > 120 && (
                  <button 
                    onClick={() => setSelectedJob(job)}
                    className="text-blue-600 hover:text-blue-800 text-sm font-semibold mb-5 flex items-center group transition-colors"
                  >
                    Read More 
                    <ChevronRight size={16} className="ml-0.5 group-hover:translate-x-0.5 transition-transform" />
                  </button>
                )}
                
                {job.recruiterId && job.recruiterId.email && (
                  <div className="flex items-center text-xs text-gray-400 mb-6 font-medium mt-auto pt-4">
                    <Clock size={14} className="mr-1.5" />
                    Posted by: {job.recruiterId.email}
                  </div>
                )}
              </div>

              <Link 
                href={`/apply/${job._id}`}
                className="block w-full text-center bg-gray-50 hover:bg-blue-600 text-gray-700 hover:text-white font-semibold py-3 rounded-xl transition-colors border border-gray-100 hover:border-blue-600"
              >
                Apply Now
              </Link>
            </div>
          ))}
        </div>
      )}

      {/* Expandable JD Modal */}
      {selectedJob && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[85vh] flex flex-col animate-in zoom-in-95 duration-200">
            
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-100">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center shrink-0">
                  <Building2 size={24} />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">{selectedJob.title}</h2>
                  <span className="text-sm font-medium text-gray-500 flex items-center mt-1">
                    <Clock size={14} className="mr-1.5" />
                    {selectedJob.recruiterId?.email || "Confidential Recruiter"}
                  </span>
                </div>
              </div>
              <button 
                onClick={() => setSelectedJob(null)}
                className="p-2 text-gray-400 hover:text-gray-900 hover:bg-gray-100 rounded-full transition-colors"
              >
                <X size={24} />
              </button>
            </div>

            {/* Modal Body (Scrollable) */}
            <div className="p-6 overflow-y-auto flex-1">
              {(() => {
                const { responsibilities, skills } = parseJobDescription(selectedJob.description);
                return (
                  <div className="space-y-8">
                    {/* Key Responsibilities */}
                    {responsibilities.length > 0 && (
                      <div>
                        <h3 className="text-sm font-bold text-gray-900 uppercase tracking-widest mb-4 flex items-center">
                          <span className="w-2 h-2 bg-blue-600 rounded-full mr-2"></span>
                          Key Responsibilities
                        </h3>
                        <ul className="space-y-3">
                          {responsibilities.map((item, idx) => (
                            <li key={idx} className="text-gray-700 text-sm leading-relaxed flex items-start">
                              <span className="text-gray-400 mr-2 mt-0.5">•</span>
                              <span>{item}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Skills Required */}
                    {skills.length > 0 && (
                      <div>
                        <h3 className="text-sm font-bold text-gray-900 uppercase tracking-widest mb-4 flex items-center">
                          <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                          Skills Required
                        </h3>
                        <ul className="space-y-3">
                          {skills.map((item, idx) => (
                            <li key={idx} className="text-gray-700 text-sm leading-relaxed flex items-start">
                              <span className="text-gray-400 mr-2 mt-0.5">•</span>
                              <span>{item}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>

            {/* Modal Footer */}
            <div className="p-6 border-t border-gray-100 bg-gray-50 rounded-b-2xl flex justify-end gap-4">
              <button 
                onClick={() => setSelectedJob(null)}
                className="px-6 py-2.5 text-sm font-semibold text-gray-700 hover:text-gray-900 hover:bg-gray-200 rounded-xl transition-colors"
              >
                Close Preview
              </button>
              <Link 
                href={`/apply/${selectedJob._id}`}
                className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-2.5 rounded-xl font-semibold transition-colors shadow-md shadow-blue-500/20"
              >
                Apply for this Role
              </Link>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
