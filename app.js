const TIMELINE = document.getElementById("timeline");

function escapeHtml(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

// Minimal markdown: paragraphs, bold, inline code, links, fenced code blocks.
function renderMarkdown(src) {
  if (!src) return "";
  const blocks = [];
  const lines = String(src).split(/\n/);
  let i = 0;
  // fenced code
  let out = "";
  let para = [];
  const flushPara = () => {
    if (para.length) {
      out += "<p>" + inline(para.join(" ")) + "</p>";
      para = [];
    }
  };
  while (i < lines.length) {
    const line = lines[i];
    if (/^```/.test(line)) {
      flushPara();
      const code = [];
      i++;
      while (i < lines.length && !/^```/.test(lines[i])) { code.push(lines[i]); i++; }
      i++;
      out += "<pre><code>" + escapeHtml(code.join("\n")) + "</code></pre>";
      continue;
    }
    if (/^#{2,3}\s+/.test(line)) {
      flushPara();
      const level = line.startsWith("###") ? "h4" : "h3";
      out += `<${level}>${inline(line.replace(/^#{2,3}\s+/, ""))}</${level}>`;
      i++;
      continue;
    }
    if (/^[-*]\s+/.test(line)) {
      flushPara();
      const items = [];
      while (i < lines.length && /^[-*]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^[-*]\s+/, ""));
        i++;
      }
      out += "<ul>" + items.map(it => "<li>" + inline(it) + "</li>").join("") + "</ul>";
      continue;
    }
    if (line.trim() === "") { flushPara(); i++; continue; }
    para.push(line);
    i++;
  }
  flushPara();
  return out;
}

function inline(s) {
  let t = escapeHtml(s);
  t = t.replace(/`([^`]+)`/g, "<code>$1</code>");
  t = t.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  t = t.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  // bare urls
  t = t.replace(/(^|[\s(])(https?:\/\/[^\s)]+)/g, '$1<a href="$2" target="_blank" rel="noopener">$2</a>');
  return t;
}

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso + (iso.length === 10 ? "T00:00:00" : ""));
  if (isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

function card(post) {
  const el = document.createElement("article");
  el.className = "card";
  const title = post.title ? escapeHtml(post.title) : "(untitled)";
  const titleHtml = post.url
    ? `<h2 class="card-title"><a href="${escapeHtml(post.url)}" target="_blank" rel="noopener">${title}</a></h2>`
    : `<h2 class="card-title">${title}</h2>`;
  const desc = post.description ? `<p class="card-desc">${inline(post.description)}</p>` : "";
  const body = post.body ? `<div class="card-body">${renderMarkdown(post.body)}</div>` : "";
  const img = post.image ? `<img class="card-image" src="${escapeHtml(post.image)}" alt="" loading="lazy" />` : "";
  const tags = (post.tags || []).map(t => `<span class="tag">${escapeHtml(t)}</span>`).join("");
  const tagsHtml = tags ? `<div class="card-tags">${tags}</div>` : "";
  const links = (post.links || []).map(l => {
    const label = (typeof l === "string") ? l : (l.label || l.text || l.title || l.url);
    const url = (typeof l === "string") ? l : l.url;
    return `<li><a href="${escapeHtml(url)}" target="_blank" rel="noopener">${escapeHtml(label)}</a></li>`;
  }).join("");
  const linksHtml = links ? `<div class="see-also"><p class="see-also-title">See also</p><ul>${links}</ul></div>` : "";
  el.innerHTML = `
    <div class="card-meta"><span class="card-date">${escapeHtml(formatDate(post.date))}</span></div>
    ${titleHtml}
    ${desc}
    ${body}
    ${img}
    ${tagsHtml}
    ${linksHtml}
  `;
  return el;
}

async function load() {
  try {
    const res = await fetch("./posts.jsonl", { cache: "no-store" });
    if (!res.ok) throw new Error("HTTP " + res.status);
    const text = await res.text();
    const posts = text
      .split(/\n/)
      .map(l => l.trim())
      .filter(Boolean)
      .map(l => { try { return JSON.parse(l); } catch (e) { console.warn("bad line:", l, e); return null; } })
      .filter(Boolean);
    posts.sort((a, b) => String(b.date || "").localeCompare(String(a.date || "")));
    TIMELINE.innerHTML = "";
    if (!posts.length) {
      TIMELINE.innerHTML = '<p class="empty">no posts yet</p>';
      return;
    }
    const frag = document.createDocumentFragment();
    posts.forEach(p => frag.appendChild(card(p)));
    TIMELINE.appendChild(frag);
  } catch (e) {
    TIMELINE.innerHTML = `<p class="error">could not load posts: ${escapeHtml(e.message)}</p>`;
  }
}

load();
