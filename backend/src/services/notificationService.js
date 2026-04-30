const { getIO, recruiterRoom, userRoom } = require("../socket");
const logger = require("../utils/logger");

const safeEmit = (room, event, payload) => {
    const io = getIO();
    if (!io) return;
    try {
        io.to(room).emit(event, payload);
    } catch (err) {
        logger.warn("socket emit failed", { event, room, error: err.message });
    }
};

const notifyRecruiterNewApplication = (recruiterId, payload) =>
    safeEmit(recruiterRoom(recruiterId), "application:new", payload);

const notifyCandidateScored = (userId, payload) =>
    safeEmit(userRoom(userId), "application:scored", payload);

module.exports = { notifyRecruiterNewApplication, notifyCandidateScored };
