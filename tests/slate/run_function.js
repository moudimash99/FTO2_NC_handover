// Runs a Slate function file as Slate does: each {{name}} replaced by the JSON of its value, the text run as a function body.
//
//   node tests/slate/run_function.js <function file> <values.json> [<output.json>]
//
// values.json: {name: value} for the bindings (queries, variables). Prints the answer as JSON, or writes it to output.json.
const fs = require('fs');

const [file, valuesFile, outFile] = process.argv.slice(2);
if (!file || !valuesFile) { console.error('usage: node tests/slate/run_function.js <function file> <values.json> [<output.json>]'); process.exit(2); }
const values = JSON.parse(fs.readFileSync(valuesFile, 'utf8'));
const text = fs.readFileSync(file, 'utf8').replace(/\{\{\s*([\w.]+)\s*\}\}/g, (_, name) => (name in values ? JSON.stringify(values[name]) : 'null'));
const t0 = Date.now();
const answer = new Function(text)();
const out = JSON.stringify({ ms: Date.now() - t0, answer: answer === undefined ? null : answer });
if (outFile) fs.writeFileSync(outFile, out); else process.stdout.write(out);
