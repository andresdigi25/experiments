const {readFileSync} = require('fs');

const data = readFileSync('books.json');
console.log(JSON.parse(data));