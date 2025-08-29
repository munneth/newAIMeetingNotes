const crypto = require('crypto');

// Generate a secure random API key
function generateApiKey() {
  // Generate 64 random bytes and convert to hex string
  const apiKey = crypto.randomBytes(32).toString('hex');
  return apiKey;
}

// Generate the API key
const apiKey = generateApiKey();

console.log('🔐 Generated Secure API Key:');
console.log('=====================================');
console.log(apiKey);
console.log('=====================================');
console.log('');
console.log('📝 Add this to your .env file:');
console.log(`USER_MEETINGS_API_KEY="${apiKey}"`);
console.log('');
console.log('🔒 Security Features:');
console.log('- 64-character random hex string');
console.log('- Cryptographically secure');
console.log('- Must be included in Authorization header');
console.log('- Never exposed in URLs or logs');
console.log('');
console.log('📡 Usage Example:');
console.log(`curl -H "Authorization: Bearer ${apiKey}" "http://localhost:3000/api/user-meetings?userId=USER_ID"`);
