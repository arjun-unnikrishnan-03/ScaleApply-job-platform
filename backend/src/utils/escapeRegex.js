const escapeRegex = (input) => String(input).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

module.exports = escapeRegex;
