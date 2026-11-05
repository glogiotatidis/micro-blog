// Renders every post body with the browser renderer from app.js, so the Python
// port in sitepage.py can be diffed against it. Optional argument: a JSON file
// holding an array of extra markdown strings to render (headings, lists...).
//
//   node check_render.js > /tmp/js.json
//   node check_render.js fixtures.json > /tmp/js.json
const fs = require("fs");
const src = fs.readFileSync(__dirname + "/app.js", "utf8");
const start = src.indexOf("function escapeHtml");
const end = src.indexOf("function formatDate");
if (start < 0 || end < 0) throw new Error("cannot find the renderer in app.js");
eval(src.slice(start, end));

const posts = {};
for (const line of fs.readFileSync(__dirname + "/posts.jsonl", "utf8").split("\n")) {
  if (!line.trim()) continue;
  const p = JSON.parse(line);
  posts[p.slug] = renderMarkdown(p.body || "");
}

let fixtures = [];
if (process.argv[2]) fixtures = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));

console.log(JSON.stringify({ posts, fixtures: fixtures.map(s => renderMarkdown(s)) }));
