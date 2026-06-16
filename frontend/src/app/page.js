"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  Sparkles, 
  Briefcase, 
  ArrowRight, 
  CheckCircle, 
  Zap, 
  BarChart3, 
  Database, 
  ShieldCheck, 
  MessageSquare 
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

export default function Home() {
  const router = useRouter();
  const { ready, isAuthenticated, role } = useAuth();



  return (
    <div className="w-full bg-gray-50 min-h-screen overflow-x-hidden font-sans">
      
      {/* Background Decorative Gradients */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[600px] pointer-events-none -z-10 overflow-hidden">
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[60%] rounded-full bg-blue-400/10 blur-[120px]"></div>
        <div className="absolute top-[-10%] right-[-10%] w-[50%] h-[60%] rounded-full bg-indigo-400/10 blur-[120px]"></div>
      </div>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16 text-center">
        {/* Release Pill */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-50 border border-blue-100 text-xs font-semibold text-blue-700 mb-8 animate-fade-in shadow-sm hover:scale-105 transition-transform duration-300">
          <Sparkles size={14} className="animate-pulse" />
          <span>Announcing ScaleApply v2.5 AI</span>
          <span className="h-3 w-px bg-blue-200"></span>
          <span className="text-blue-500 font-medium">Powered by Groq</span>
        </div>

        {/* Headline */}
        <h1 className="text-4xl sm:text-6xl font-extrabold text-gray-900 tracking-tight max-w-4xl mx-auto leading-[1.1] mb-6">
          The Intelligent Career Portal &{" "}
          <span className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent">
            Recruiting System
          </span>
        </h1>

        {/* Subhead */}
        <p className="text-lg sm:text-xl text-gray-500 max-w-2xl mx-auto leading-relaxed mb-10">
          Automate resume parsing, calculate instant skill gap analyses, and converse with a RAG-powered knowledge assistant. Built for scale.
        </p>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row gap-4 items-center justify-center mb-16">
          {!ready ? (
            <div className="animate-pulse bg-gray-200 h-14 w-64 rounded-xl"></div>
          ) : isAuthenticated ? (
            <>
              <Link 
                href={role === "recruiter" ? "/dashboard" : "/jobs"} 
                className="w-full sm:w-auto px-8 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold rounded-xl shadow-lg shadow-blue-500/20 hover:scale-[1.03] active:scale-95 transition-all duration-300 flex items-center justify-center gap-2 group text-center"
              >
                {role === "recruiter" ? "Go to Dashboard" : "Browse Opportunities"}
                <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link 
                href={role === "recruiter" ? "/post-job" : "/profile"} 
                className="w-full sm:w-auto px-8 py-4 bg-white border border-gray-200 text-gray-700 font-bold rounded-xl shadow-sm hover:bg-gray-50 active:scale-95 transition-all duration-300 text-center"
              >
                {role === "recruiter" ? "Post a New Job" : "View My Profile"}
              </Link>
            </>
          ) : (
            <>
              <Link 
                href="/register" 
                className="w-full sm:w-auto px-8 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold rounded-xl shadow-lg shadow-blue-500/20 hover:scale-[1.03] active:scale-95 transition-all duration-300 flex items-center justify-center gap-2 group text-center"
              >
                Get Started Free
                <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link 
                href="/login" 
                className="w-full sm:w-auto px-8 py-4 bg-white border border-gray-200 text-gray-700 font-bold rounded-xl shadow-sm hover:bg-gray-50 active:scale-95 transition-all duration-300 text-center"
              >
                Sign In to Platform
              </Link>
            </>
          )}
        </div>

        {/* Interface Visual Mockup */}
        <div className="max-w-5xl mx-auto bg-white rounded-2xl border border-gray-200 shadow-2xl p-6 sm:p-8 relative overflow-hidden group hover:border-gray-300 transition-all duration-300">
          {/* Header Row */}
          <div className="flex items-center justify-between pb-6 border-b border-gray-100 mb-6">
            <div className="flex items-center gap-2">
              <span className="h-3.5 w-3.5 rounded-full bg-red-400"></span>
              <span className="h-3.5 w-3.5 rounded-full bg-yellow-400"></span>
              <span className="h-3.5 w-3.5 rounded-full bg-green-400"></span>
            </div>
            <div className="bg-gray-100 rounded-lg text-xs text-gray-500 font-medium px-6 py-1.5 border border-gray-200/50">
              platform.scaleapply.ai/dashboard
            </div>
            <div className="w-10"></div>
          </div>

          {/* Grid Content Mockup */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
            {/* Mock Stat Card 1 */}
            <div className="bg-gray-50 p-5 rounded-xl border border-gray-200/60 shadow-sm flex flex-col gap-2">
              <div className="flex justify-between items-center text-gray-400">
                <span className="text-xs font-bold uppercase tracking-wider">AI Accuracy Rate</span>
                <Sparkles size={16} className="text-blue-500" />
              </div>
              <span className="text-3xl font-extrabold text-gray-900">98.4%</span>
              <span className="text-xs text-green-600 font-semibold flex items-center gap-1">
                +1.2% this quarter due to Gemini 2.5 Upgrade
              </span>
            </div>

            {/* Mock Stat Card 2 */}
            <div className="bg-gray-50 p-5 rounded-xl border border-gray-200/60 shadow-sm flex flex-col gap-2">
              <div className="flex justify-between items-center text-gray-400">
                <span className="text-xs font-bold uppercase tracking-wider">Candidate Scores calculated</span>
                <BarChart3 size={16} className="text-indigo-500" />
              </div>
              <span className="text-3xl font-extrabold text-gray-900">14,280</span>
              <span className="text-xs text-gray-500 font-medium">Average matching speed: 1.4 seconds</span>
            </div>

            {/* Mock Stat Card 3 */}
            <div className="bg-gray-50 p-5 rounded-xl border border-gray-200/60 shadow-sm flex flex-col gap-2">
              <div className="flex justify-between items-center text-gray-400">
                <span className="text-xs font-bold uppercase tracking-wider">System Up-Time</span>
                <ShieldCheck size={16} className="text-green-500" />
              </div>
              <span className="text-3xl font-extrabold text-gray-900">99.99%</span>
              <span className="text-xs text-green-600 font-semibold">Active globally across multi-regions</span>
            </div>
          </div>

          {/* Bottom mock preview block */}
          <div className="mt-6 bg-slate-900 text-white rounded-xl p-5 text-left border border-slate-800 shadow-inner font-mono text-xs overflow-x-auto relative">
            <span className="absolute top-3 right-3 text-[10px] bg-slate-800 text-slate-400 font-semibold px-2 py-0.5 rounded uppercase tracking-widest border border-slate-700">
              Response Log
            </span>
            <div className="text-green-400">✔ Uploaded resume: &apos;Senior_Software_Engineer_CV.pdf&apos;</div>
            <div className="text-blue-300">➜ Initiating parsing pipeline... model version: gemini-2.5-flash</div>
            <div className="text-gray-300">➜ Extracted 12 core skills (React, Node.js, Redis, MongoDB, Docker, Python...)</div>
            <div className="text-indigo-400">➜ Running semantic ATS Match against Job Listing: &apos;Lead Backend Engineer&apos;</div>
            <div className="text-yellow-400">➜ MATCH CALCULATED: Score 92/100, Skill Gap identified: Python, Kubernetes</div>
            <div className="text-green-400">✔ Syncing real-time WebSocket alert to recruiter... SUCCESS.</div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="bg-white border-y border-gray-200/80 py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-xs font-bold text-blue-600 uppercase tracking-widest mb-3">Enterprise Core Features</h2>
            <p className="text-3xl sm:text-4xl font-bold text-gray-900 tracking-tight">
              A Complete Suite of Artificial Intelligence for modern HR Teams
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Feature 1 */}
            <div className="p-6 rounded-2xl border border-gray-100 bg-gray-50/50 hover:bg-white hover:border-gray-200 hover:shadow-xl transition-all duration-300 flex flex-col h-full group">
              <div className="bg-gradient-to-tr from-blue-50 to-indigo-50 text-blue-600 p-3 rounded-xl w-fit mb-5 group-hover:scale-110 transition-transform">
                <Sparkles size={22} />
              </div>
              <h3 className="font-bold text-lg text-gray-900 mb-2">ATS Matching Engine</h3>
              <p className="text-gray-500 text-sm leading-relaxed">
                Compute candidate fit using semantic modeling instead of rigid keywords. Generate match scores instantly.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="p-6 rounded-2xl border border-gray-100 bg-gray-50/50 hover:bg-white hover:border-gray-200 hover:shadow-xl transition-all duration-300 flex flex-col h-full group">
              <div className="bg-gradient-to-tr from-indigo-50 to-purple-50 text-indigo-600 p-3 rounded-xl w-fit mb-5 group-hover:scale-110 transition-transform">
                <MessageSquare size={22} />
              </div>
              <h3 className="font-bold text-lg text-gray-900 mb-2">RAG Knowledge Base</h3>
              <p className="text-gray-500 text-sm leading-relaxed">
                A context-aware floating chat widget answering user, recruiter, and career questions in real time.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="p-6 rounded-2xl border border-gray-100 bg-gray-50/50 hover:bg-white hover:border-gray-200 hover:shadow-xl transition-all duration-300 flex flex-col h-full group">
              <div className="bg-gradient-to-tr from-purple-50 to-pink-50 text-purple-600 p-3 rounded-xl w-fit mb-5 group-hover:scale-110 transition-transform">
                <Database size={22} />
              </div>
              <h3 className="font-bold text-lg text-gray-900 mb-2">Resume Parsing</h3>
              <p className="text-gray-500 text-sm leading-relaxed">
                Extract structured JSON profiles directly from raw PDF, DOC, or DOCX resumes in seconds.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="p-6 rounded-2xl border border-gray-100 bg-gray-50/50 hover:bg-white hover:border-gray-200 hover:shadow-xl transition-all duration-300 flex flex-col h-full group">
              <div className="bg-gradient-to-tr from-blue-50 to-emerald-50 text-emerald-600 p-3 rounded-xl w-fit mb-5 group-hover:scale-110 transition-transform">
                <Zap size={22} />
              </div>
              <h3 className="font-bold text-lg text-gray-900 mb-2">Real-Time Alerts</h3>
              <p className="text-gray-500 text-sm leading-relaxed">
                Driven by WebSockets, immediately alert users when AI scores their applications or updates profiles.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-xs font-bold text-indigo-600 uppercase tracking-widest mb-3">Transparent Plans</h2>
          <p className="text-3xl sm:text-4xl font-bold text-gray-900 tracking-tight">
            Designed to scale for individuals and teams
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {/* Plan 1 */}
          <div className="bg-white p-8 rounded-2xl border border-gray-200 shadow-sm flex flex-col h-full hover:border-gray-300 transition-all">
            <h3 className="font-bold text-xl text-gray-900 mb-2">Basic</h3>
            <p className="text-gray-500 text-sm mb-6 font-medium">For single applicants exploring jobs.</p>
            <div className="flex items-baseline gap-1 mb-8">
              <span className="text-4xl font-extrabold text-gray-900">$0</span>
              <span className="text-gray-400 text-sm font-semibold">/ forever</span>
            </div>
            <ul className="space-y-4 mb-8 text-sm text-gray-600 font-semibold flex-1">
              <li className="flex items-center gap-2.5">
                <CheckCircle size={16} className="text-green-500" />
                Explore Active Job listings
              </li>
              <li className="flex items-center gap-2.5">
                <CheckCircle size={16} className="text-green-500" />
                Up to 5 AI resume parses
              </li>
              <li className="flex items-center gap-2.5">
                <CheckCircle size={16} className="text-green-500" />
                Basic candidate profiles
              </li>
            </ul>
            <Link 
              href="/register" 
              className="block w-full text-center bg-gray-50 hover:bg-gray-100 text-gray-800 font-bold py-3.5 rounded-xl border border-gray-200/80 transition-colors"
            >
              Get Started
            </Link>
          </div>

          {/* Plan 2 (Featured) */}
          <div className="bg-white p-8 rounded-2xl border-2 border-blue-600 shadow-xl flex flex-col h-full relative transform scale-[1.02] md:-translate-y-2">
            <div className="absolute top-0 right-1/2 translate-x-1/2 -translate-y-1/2 bg-blue-600 text-white text-[10px] font-extrabold uppercase px-3 py-1 rounded-full tracking-widest shadow-md">
              Most Popular
            </div>
            <h3 className="font-bold text-xl text-gray-900 mb-2">Pro Recruiter</h3>
            <p className="text-gray-500 text-sm mb-6 font-medium">For scaling startups and active recruiters.</p>
            <div className="flex items-baseline gap-1 mb-8">
              <span className="text-4xl font-extrabold text-gray-900">$89</span>
              <span className="text-gray-400 text-sm font-semibold">/ month</span>
            </div>
            <ul className="space-y-4 mb-8 text-sm text-gray-600 font-semibold flex-1">
              <li className="flex items-center gap-2.5">
                <CheckCircle size={16} className="text-blue-600" />
                Unlimited job listings
              </li>
              <li className="flex items-center gap-2.5">
                <CheckCircle size={16} className="text-blue-600" />
                Instant AI Score matching
              </li>
              <li className="flex items-center gap-2.5">
                <CheckCircle size={16} className="text-blue-600" />
                Full Skill Gap Analysis
              </li>
              <li className="flex items-center gap-2.5">
                <CheckCircle size={16} className="text-blue-600" />
                Floating RAG chatbot access
              </li>
            </ul>
            <Link 
              href="/register" 
              className="block w-full text-center bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold py-3.5 rounded-xl shadow-md shadow-blue-500/10 transition-all duration-300"
            >
              Start 14-Day Free Trial
            </Link>
          </div>

          {/* Plan 3 */}
          <div className="bg-white p-8 rounded-2xl border border-gray-200 shadow-sm flex flex-col h-full hover:border-gray-300 transition-all">
            <h3 className="font-bold text-xl text-gray-900 mb-2">Enterprise</h3>
            <p className="text-gray-500 text-sm mb-6 font-medium">For large HR organizations & companies.</p>
            <div className="flex items-baseline gap-1 mb-8">
              <span className="text-4xl font-extrabold text-gray-900">Custom</span>
              <span className="text-gray-400 text-sm font-semibold">/ billing</span>
            </div>
            <ul className="space-y-4 mb-8 text-sm text-gray-600 font-semibold flex-1">
              <li className="flex items-center gap-2.5">
                <CheckCircle size={16} className="text-green-500" />
                Dedicated API keys
              </li>
              <li className="flex items-center gap-2.5">
                <CheckCircle size={16} className="text-green-500" />
                Custom model endpoints
              </li>
              <li className="flex items-center gap-2.5">
                <CheckCircle size={16} className="text-green-500" />
                SLA & security contracts
              </li>
              <li className="flex items-center gap-2.5">
                <CheckCircle size={16} className="text-green-500" />
                Dedicated Customer Success
              </li>
            </ul>
            <Link 
              href="mailto:sales@scaleapply.ai" 
              className="block w-full text-center bg-gray-900 hover:bg-gray-800 text-white font-bold py-3.5 rounded-xl transition-colors"
            >
              Contact Sales
            </Link>
          </div>
        </div>
      </section>

      {/* CTA Footer Wrapper */}
      <section className="bg-gradient-to-r from-blue-900 to-indigo-900 text-white py-20 text-center relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-blue-800/30 via-transparent to-transparent pointer-events-none"></div>
        <div className="max-w-4xl mx-auto px-4 sm:px-6 relative z-10">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">Ready to automate your recruiting?</h2>
          <p className="text-blue-100 max-w-xl mx-auto mb-8 text-sm sm:text-base font-medium">
            Join thousands of modern recruiters and job applicants saving hours every week with ScaleApply.
          </p>
          <Link 
            href={isAuthenticated ? (role === "recruiter" ? "/dashboard" : "/jobs") : "/register"} 
            className="inline-flex items-center gap-2 px-8 py-4 bg-white text-blue-900 font-bold rounded-xl shadow-lg hover:scale-105 active:scale-95 transition-all duration-300"
          >
            {isAuthenticated ? "Go to Workspace" : "Create Your Account"}
            <ArrowRight size={18} />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-10 text-center text-xs text-gray-400 font-medium">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="bg-blue-600 text-white p-1.5 rounded-lg">
              <Briefcase size={12} />
            </div>
            <span className="font-extrabold text-sm text-gray-900">ScaleApply</span>
          </div>
          <div>© {new Date().getFullYear()} ScaleApply Inc. All rights reserved. Made for enterprise recruiting.</div>
          <div className="flex gap-4">
            <Link href="#" className="hover:text-gray-600 transition-colors">Privacy Policy</Link>
            <Link href="#" className="hover:text-gray-600 transition-colors">Terms of Service</Link>
            <Link href="#" className="hover:text-gray-600 transition-colors">Support</Link>
          </div>
        </div>
      </footer>

    </div>
  );
}
