const fs = require('fs');
const csv = fs.readFileSync('audit_log.csv', 'utf8');
const lines = csv.split(/\r?\n/).slice(1).filter(l => l.trim() !== "");
const values = lines.slice(0, 100).map(l => l.split(',')[1] || "0");
const input = {
    "event_values": values,
    "event_index": "42",
    "event_value": values[42],
    "salt": "123456789"
};
fs.writeFileSync('input.json', JSON.stringify(input));
console.log("🎯 input.json is PERFECT.");
