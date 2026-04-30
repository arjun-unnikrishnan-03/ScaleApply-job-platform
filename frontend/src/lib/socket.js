import { io } from "socket.io-client";

const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

let socket = null;

export const connectSocket = (token) => {
    if (!token) return null;
    if (socket && socket.connected) return socket;
    socket = io(baseURL, {
        auth: { token },
        transports: ["websocket"],
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000
    });
    return socket;
};

export const disconnectSocket = () => {
    if (socket) {
        socket.disconnect();
        socket = null;
    }
};

export const getSocket = () => socket;
