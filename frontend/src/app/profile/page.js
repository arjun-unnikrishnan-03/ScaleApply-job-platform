"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { UserCircle, UploadCloud, CheckCircle, Sparkles, Briefcase, GraduationCap, Code, Zap, MapPin, ArrowRight } from "lucide-react";
import toast from "react-hot-toast";
import api from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";

export default function ProfilePage() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [profile, setProfile] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const router = useRouter();
  const { ready, isAuthenticated, role } = useAuth();

  useEffect(() => {
    if (!ready) return;
    if (!isAuthenticated) router.replace("/login");
    else if (role !== "candidate") router.replace("/dashboard");
  }, [ready, isAuthenticated, role, router]);

  // Load saved profile on mount
  useEffect(() => {
    if (!ready || !isAuthenticated) return;
    const fetchProfile = async () => {
      try {
        const { data } = await api.get("/api/auth/me");
        if (data?.candidateProfile) {
          setProfile(data.candidateProfile);
          fetchRecommendations();
        }
      } catch (err) {
        // No profile yet, that's fine
      } finally {
        setFetching(false);
      }
    };
    fetchProfile();
  }, [ready, isAuthenticated]);

  const fetchRecommendations = async () => {
    try {
      const { data } = await api.get("/api/ai/recommendations");
      setRecommendations(data);
    } catch (err) {
      // Non-critical, ignore silently
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files?.[0]) setFile(e.target.files[0]);
  };

  const handleAutoFill = async (e) => {
    e.preventDefault();
    if (!file) {
      toast.error("Please select a resume file first.");
      return;
    }
    
    setLoading(true);
    const formData = new FormData();
    formData.append("resume", file);

    try {
      const { data } = await api.post("/api/ai/resume/analyze", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setProfile(data.profile);
      toast.success("Profile auto-filled successfully via AI!");
      setFile(null);
      // Fetch job recommendations after profile is created
      fetchRecommendations();
    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to analyze resume.");
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <UserCircle className="text-blue-600" size={32} />
          My Candidate Profile
        </h1>
        <p className="text-gray-500 mt-2">Manage your professional details and let AI build your profile.</p>
      </div>

      {fetching ? (
        <div className="flex items-center justify-center py-16">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <>
          {/* AI Upload Section — always visible, collapsed if profile exists */}
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-100 p-8 rounded-2xl shadow-sm relative overflow-hidden">
            <div className="absolute top-0 right-0 p-6 opacity-10">
              <Sparkles size={120} className="text-blue-600" />
            </div>

            <h2 className="text-xl font-bold text-blue-900 mb-2 flex items-center gap-2">
              <Sparkles size={20} className="text-blue-600" />
              {profile ? "Update Profile with AI" : "Auto-Fill with AI"}
            </h2>
            <p className="text-blue-700 text-sm mb-6 max-w-xl">
              {profile
                ? "Upload a new resume to refresh your profile with the latest AI analysis."
                : "Upload your resume and our AI will automatically extract your skills, experience, and education to build your profile instantly."}
            </p>

            <form onSubmit={handleAutoFill} className="relative z-10 flex flex-col sm:flex-row gap-4 items-start sm:items-center">
              <div className="relative flex-1 w-full bg-white border-2 border-dashed border-blue-200 hover:border-blue-400 rounded-xl p-4 transition-colors group text-center cursor-pointer">
                <input
                  type="file"
                  accept=".pdf,.doc,.docx"
                  onChange={handleFileChange}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                <div className="flex items-center justify-center gap-3 text-blue-600 font-medium text-sm">
                  <UploadCloud size={20} />
                  {file ? file.name : "Select Resume to Auto-Fill"}
                </div>
              </div>
              
              <button
                type="submit"
                disabled={loading || !file}
                className="w-full sm:w-auto bg-blue-600 hover:bg-blue-700 text-white font-semibold py-4 px-8 rounded-xl transition-all shadow-md shadow-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    Analyzing...
                  </>
                ) : (
                  "Generate Profile"
                )}
              </button>
            </form>
          </div>

          {/* Profile Display Section */}
          {profile && (
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="bg-gray-50 border-b border-gray-200 px-8 py-6 flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">{profile.contact_info?.name || "Anonymous User"}</h2>
                  <p className="text-gray-500 text-sm mt-1">{profile.contact_info?.email}</p>
                </div>
                <div className="bg-green-100 text-green-800 text-xs font-bold px-3 py-1.5 rounded-full flex items-center gap-1.5">
                  <CheckCircle size={14} /> AI Verified
                </div>
              </div>

              <div className="p-8 space-y-8">
                {/* Summary */}
                <div className="space-y-3">
                  <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider">Professional Summary</h3>
                  <p className="text-gray-700 leading-relaxed text-sm">{profile.summary}</p>
                </div>

                {/* Skills */}
                <div className="space-y-3">
                  <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider flex items-center gap-2">
                    <Code size={16} /> Technical Skills
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {profile.skills?.technical?.map((skill, i) => (
                      <span key={i} className="bg-blue-50 border border-blue-100 text-blue-700 px-3 py-1 rounded-md text-xs font-medium">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Experience */}
                <div className="space-y-4">
                  <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider flex items-center gap-2">
                    <Briefcase size={16} /> Work Experience
                  </h3>
                  <div className="space-y-6">
                    {profile.experience?.map((exp, i) => (
                      <div key={i} className="relative pl-6 border-l-2 border-gray-100">
                        <div className="absolute w-3 h-3 bg-gray-200 rounded-full -left-[7px] top-1.5"></div>
                        <h4 className="text-base font-bold text-gray-900">{exp.title}</h4>
                        <p className="text-sm text-gray-500 font-medium mb-2">{exp.company} • {exp.start_date} - {exp.end_date}</p>
                        <ul className="list-disc pl-5 space-y-1">
                          {exp.highlights?.map((highlight, j) => (
                            <li key={j} className="text-sm text-gray-600 leading-relaxed">{highlight}</li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Education */}
                <div className="space-y-4">
                  <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider flex items-center gap-2">
                    <GraduationCap size={16} /> Education
                  </h3>
                  <div className="grid sm:grid-cols-2 gap-4">
                    {profile.education?.map((edu, i) => (
                      <div key={i} className="bg-gray-50 p-4 rounded-xl border border-gray-100">
                        <h4 className="font-bold text-gray-900 text-sm">{edu.degree}</h4>
                        <p className="text-sm text-gray-600">{edu.institution}</p>
                        <p className="text-xs text-gray-400 mt-1">{edu.graduation_date}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Job Recommendations Section */}
          {recommendations?.recommendations?.length > 0 && (
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="px-8 py-6 border-b border-gray-100 flex items-center gap-3">
                <div className="bg-amber-100 p-2 rounded-lg">
                  <Zap size={20} className="text-amber-600" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-gray-900">Jobs Matched For You</h2>
                  <p className="text-sm text-gray-500">Based on your skills: {recommendations.profile?.skills?.join(", ")}</p>
                </div>
              </div>
              <div className="divide-y divide-gray-50">
                {recommendations.recommendations.map((job) => (
                  <div key={job._id} className="px-8 py-5 flex items-start justify-between gap-4 hover:bg-gray-50 transition-colors">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="font-bold text-gray-900 text-sm">{job.title}</h3>
                        {job.alreadyApplied && (
                          <span className="bg-green-100 text-green-700 text-[10px] font-bold px-2 py-0.5 rounded-full">Applied</span>
                        )}
                      </div>
                      <div className="flex items-center gap-3 text-xs text-gray-400 mt-1">
                        <span className="font-medium text-gray-600">{job.company}</span>
                        <span className="flex items-center gap-1"><MapPin size={10} />{job.location}</span>
                      </div>
                      {job.matchedSkills?.length > 0 && (
                        <div className="flex gap-1.5 flex-wrap mt-2">
                          {job.matchedSkills.map((s, i) => (
                            <span key={i} className="bg-blue-50 text-blue-600 text-[10px] font-semibold px-2 py-0.5 rounded border border-blue-100">{s}</span>
                          ))}
                        </div>
                      )}
                    </div>
                    {!job.alreadyApplied && (
                      <button
                        onClick={() => router.push(`/apply/${job._id}`)}
                        className="shrink-0 flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-4 py-2 rounded-lg transition-all"
                      >
                        Apply <ArrowRight size={12} />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
