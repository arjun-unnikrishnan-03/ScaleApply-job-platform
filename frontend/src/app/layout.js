import "./globals.css";
import Navbar from "@/components/Navbar";
import ChatWidget from "@/components/ChatWidget";
import { Toaster } from "react-hot-toast";
import { AuthProvider } from "@/contexts/AuthContext";

export const metadata = {
  title: "ScaleApply - Premium AI-Powered Job Platform",
  description: "Scale your recruiting and job applications with enterprise-grade AI matching, parsing, and real-time support."
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="bg-gray-50 min-h-screen text-gray-900 font-sans antialiased">
        <AuthProvider>
          <Toaster position="top-right" />
          <Navbar />
          <main className="w-full">
            {children}
          </main>
          <ChatWidget />
        </AuthProvider>
      </body>
    </html>
  );
}
