const fs = require('fs');
// 1. Read CSV
const csv = fs.readFileSync('audit_log.csv', 'utf8');
const rows = csv.split(/\r?\n/).filter(line => line.trim() !== "");
// 2. Extract column 2, skip header, force exactly 100
const rawValues = rows.slice(1).map(row => row.split(',')[1]);
const event_values = rawValues.slice(0, 100).map(v => String(v || "0"));

// 3. Match the Circuit exactly
const cleanInput = {
    event_values: event_values,
    event_index: "42",
    event_value: event_values[42],
    salt: "123456789"
};

console.log(`📊 Input check: ${cleanInput.event_values.length} items.`);
fs.writeFileSync('input.json', JSON.stringify(cleanInput));
console.log("✅ input.json rewritten perfectly.");
