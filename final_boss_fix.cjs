const fs = require('fs');

// 1. Load Data
const csv = fs.readFileSync('audit_log.csv', 'utf8');
const rows = csv.split(/\r?\n/).filter(line => line.trim() !== "");
const rawValues = rows.slice(1).map(row => row.split(',')[1]);
const event_values = rawValues.slice(0, 100).map(v => String(v || "0"));

// 2. Prepare the exact inputs the 'main' component expects
const input = {
    "event_values": event_values,
    "event_index": "42",      // Must be a string for Circom
    "event_value": event_values[42], 
    "salt": "123456789"
};

fs.writeFileSync('input.json', JSON.stringify(input));
console.log("🎯 Input.json matched to 'main' component requirements.");

const { execSync } = require('child_process');
try {
    // 3. Generate the witness
    execSync('node build/AuditTrail/AuditTrail_js/generate_witness.cjs build/AuditTrail/AuditTrail_js/AuditTrail.wasm input.json witness.wtns', {stdio: 'inherit'});
    console.log("🚀 SUCCESS! witness.wtns is born.");
} catch (e) {
    console.log("❌ Still a mismatch. Check if 'trail_root' or 'event_hash' are also inputs.");
}
