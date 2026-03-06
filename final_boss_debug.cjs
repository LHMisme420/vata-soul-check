const fs = require('fs');
const input = JSON.parse(fs.readFileSync('input.json', 'utf8'));

console.log("🔍 DEBUGGING INPUT.JSON:");
console.log("- event_values length:", input.event_values.length);
console.log("- Keys present:", Object.keys(input).join(", "));

const { execSync } = require('child_process');
try {
    console.log("🚀 Attempting Witness Generation...");
    execSync('node build/AuditTrail/AuditTrail_js/generate_witness.cjs build/AuditTrail/AuditTrail_js/AuditTrail.wasm input.json witness.wtns', {stdio: 'inherit'});
} catch (e) {
    console.log("❌ Execution Failed.");
}
