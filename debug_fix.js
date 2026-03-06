const fs = require('fs');

// 1. Read the CSV and get raw values
const csv = fs.readFileSync('audit_log.csv', 'utf8');
const rows = csv.split(/\r?\n/).filter(line => line.trim() !== "");
// Skip header, grab column 2 (index 1)
const rawValues = rows.slice(1).map(row => row.split(',')[1]);

// 2. FORCE EXACTLY 100 STRINGS (Circom prefers strings for big numbers)
const event_values = rawValues.slice(0, 100).map(v => String(v || "0"));

// 3. Construct the MINIMAL object (No extra fields allowed!)
const cleanInput = {
    event_values: event_values,
    event_index: "42",
    event_value: event_values[42],
    salt: "123456789"
};

// 4. Verify count one last time before writing
console.log(`📊 Array check: ${cleanInput.event_values.length} items`);

fs.writeFileSync('input.json', JSON.stringify(cleanInput));
console.log("✅ input.json written with ZERO extra metadata.");
