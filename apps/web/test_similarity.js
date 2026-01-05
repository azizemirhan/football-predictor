
const { distance } = require('fastest-levenshtein');

function normalizeName(name) {
  if (!name) return '';
  return name.toLowerCase()
    .replace(/ü/g, 'u')
    .replace(/ğ/g, 'g')
    .replace(/ı/g, 'i')
    .replace(/ş/g, 's')
    .replace(/ç/g, 'c')
    .replace(/ö/g, 'o')
    .replace(/[^a-z0-9 ]/g, '') 
    .trim();
}

const s1 = "Man. City";
const s2 = "Manchester City";

const n1 = normalizeName(s1);
const n2 = normalizeName(s2);

console.log(`Original: "${s1}" vs "${s2}"`);
console.log(`Normalized: "${n1}" vs "${n2}"`);
console.log(`Distance: ${distance(n1, n2)}`);

const s3 = "Arsenal";
const s4 = "Arsenal FC";
console.log(`Distance Arsenal: ${distance(normalizeName(s3), normalizeName(s4))}`);
