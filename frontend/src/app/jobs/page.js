"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Briefcase, Building2, Clock } from "lucide-react";
import { isAuthenticated } from "@/utils/auth";

export default function JobsPage() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }

    const fetchJobs = async () => {
      try {
        const response = await axios.get("http://localhost:5000/api/jobs");
        setJobs(response.data);
      } catch (error) {
        console.error("Failed to fetch jobs:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchJobs();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
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
                <p className="text-gray-500 text-sm line-clamp-3 mb-4 leading-relaxed">
                  {job.description}
                </p>
                
                {job.recruiterId && job.recruiterId.email && (
                  <div className="flex items-center text-xs text-gray-400 mb-6 font-medium">
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
    </div>
  );
}
