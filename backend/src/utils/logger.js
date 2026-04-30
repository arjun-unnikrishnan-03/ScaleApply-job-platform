const ts = () => new Date().toISOString();

const log = (level, message, meta) => {
    const payload = { ts: ts(), level, message };
    if (meta) payload.meta = meta;
    const out = level === "error" || level === "warn" ? console.error : console.log;
    out(JSON.stringify(payload));
};

module.exports = {
    info: (msg, meta) => log("info", msg, meta),
    warn: (msg, meta) => log("warn", msg, meta),
    error: (msg, meta) => log("error", msg, meta)
};
