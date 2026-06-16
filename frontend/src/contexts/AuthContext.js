"use client";

import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { connectSocket, disconnectSocket } from "@/lib/socket";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [ready, setReady] = useState(false);
    const router = useRouter();

    useEffect(() => {
        const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
        const role = typeof window !== "undefined" ? localStorage.getItem("role") : null;
        const userId = typeof window !== "undefined" ? localStorage.getItem("userId") : null;
        if (token && role) {
            // eslint-disable-next-line react-hooks/set-state-in-effect -- hydrating from localStorage which is unavailable during SSR
            setUser({ token, role, id: userId });
            connectSocket(token);
        }
        setReady(true);
        return () => disconnectSocket();
    }, []);

    const login = useCallback(async (email, password) => {
        const { data } = await api.post("/api/auth/login", { email, password });
        localStorage.setItem("token", data.token);
        localStorage.setItem("role", data.role);
        localStorage.setItem("userId", data.id);
        setUser({ token: data.token, role: data.role, id: data.id });
        connectSocket(data.token);
        router.push(data.role === "recruiter" ? "/dashboard" : "/jobs");
        return data;
    }, [router]);

    const logout = useCallback(() => {
        localStorage.removeItem("token");
        localStorage.removeItem("role");
        localStorage.removeItem("userId");
        disconnectSocket();
        setUser(null);
        router.push("/login");
    }, [router]);

    return (
        <AuthContext.Provider value={{ user, ready, login, logout, isAuthenticated: !!user, role: user?.role || null }}>
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
    return ctx;
};
