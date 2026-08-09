#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const planPath = path.join(root, "threads-content-plan.json");
const graphBase = (process.env.THREADS_GRAPH_BASE || "https://graph.threads.net").replace(/\/+$/, "");
const accessToken = process.env.THREADS_ACCESS_TOKEN || "";
const expectedUsername = process.env.THREADS_EXPECTED_USERNAME || "cv.argatirta";
const assetBase = (process.env.PUBLIC_ASSET_BASE_URL || "").replace(/\/+$/, "");
const mode = argument("mode") || process.env.ARGA_TIRTA_THREADS_MODE || "due";
const requestedId = argument("post-id") || process.env.ARGA_TIRTA_THREADS_POST_ID || "";
const now = new Date(process.env.ARGA_TIRTA_NOW || Date.now());

function argument(name) {
  const exact = `--${name}`;
  const prefix = `${exact}=`;
  const index = process.argv.indexOf(exact);
  if (index >= 0) return process.argv[index + 1];
  return process.argv.find((value) => value.startsWith(prefix))?.slice(prefix.length);
}

function dueAt(item) {
  return new Date(`${item.date}T${item.time_wib}:00+07:00`);
}

function selectItem(items) {
  if (requestedId) {
    const item = items.find((entry) => entry.id === requestedId);
    if (!item) throw new Error(`Threads queue item ${requestedId} was not found`);
    return item;
  }
  return items
    .filter((item) => item.status === "queued_auto" && item.approval_status === "approved")
    .map((item) => ({ item, due: dueAt(item) }))
    .filter(({ due }) => due <= now)
    .sort((a, b) => a.due - b.due || a.item.id.localeCompare(b.item.id))[0]?.item;
}

function requireConfig(item) {
  const missing = [];
  if (!accessToken) missing.push("THREADS_ACCESS_TOKEN");
  if (item?.media_type === "IMAGE" && !assetBase) missing.push("PUBLIC_ASSET_BASE_URL");
  if (missing.length) throw new Error(`Missing configuration: ${missing.join(", ")}`);
}

async function responseJson(response) {
  const text = await response.text();
  let payload;
  try {
    payload = text ? JSON.parse(text) : {};
  } catch {
    payload = { raw: text.slice(0, 500) };
  }
  if (!response.ok || payload.error) {
    const message = payload.error?.error_user_msg || payload.error?.message || payload.message || `HTTP ${response.status}`;
    const code = payload.error?.code ? ` [code ${payload.error.code}]` : "";
    throw new Error(`${message}${code}`);
  }
  return payload;
}

async function graph(pathname, params = {}, method = "GET") {
  const url = new URL(`${graphBase}/${pathname.replace(/^\/+/, "")}`);
  const values = new URLSearchParams({ ...params, access_token: accessToken });
  if (method === "GET") {
    for (const [key, value] of values) url.searchParams.set(key, value);
    return responseJson(await fetch(url, { headers: { accept: "application/json" } }));
  }
  return responseJson(await fetch(url, {
    method,
    headers: { accept: "application/json", "content-type": "application/x-www-form-urlencoded" },
    body: values,
  }));
}

async function account() {
  const profile = await graph("me", { fields: "id,username,name,threads_biography,threads_profile_picture_url" });
  if (expectedUsername && profile.username !== expectedUsername) {
    throw new Error(`Threads token resolved to @${profile.username || "unknown"}, expected @${expectedUsername}`);
  }
  return profile;
}

function assetUrl(item) {
  if (!item.asset) throw new Error(`${item.id} has no asset`);
  const url = new URL(`${assetBase}/${String(item.asset).replace(/^\/+/, "")}`);
  url.searchParams.set("v", item.id);
  return url.toString();
}

async function verifyAsset(url) {
  const response = await fetch(url, { method: "HEAD", redirect: "follow" });
  if (!response.ok) throw new Error(`Asset returned HTTP ${response.status}: ${url}`);
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.startsWith("image/")) throw new Error(`Asset is not an image: ${url}`);
  return { url: response.url, content_type: contentType, bytes: Number(response.headers.get("content-length") || 0) };
}

async function waitForContainer(id) {
  const deadline = Date.now() + 120_000;
  while (Date.now() < deadline) {
    const result = await graph(id, { fields: "id,status,error_message" });
    if (["FINISHED", "PUBLISHED"].includes(result.status)) return result;
    if (["ERROR", "EXPIRED"].includes(result.status)) throw new Error(`Threads container ${result.status}: ${result.error_message || "unknown"}`);
    await new Promise((resolve) => setTimeout(resolve, 4000));
  }
  throw new Error(`Timed out waiting for Threads container ${id}`);
}

async function readThread(id) {
  for (let attempt = 0; attempt < 6; attempt += 1) {
    try {
      return await graph(id, { fields: "id,text,permalink,timestamp,username,media_type" });
    } catch (error) {
      if (attempt === 5) throw error;
      await new Promise((resolve) => setTimeout(resolve, 2000));
    }
  }
}

async function recentThreads() {
  const result = await graph("me/threads", { fields: "id,text,permalink,timestamp,username,media_type", limit: "100" });
  return result.data || [];
}

async function findExisting(item) {
  const expected = item.text.replace(/\s+/g, " ").trim().toLowerCase();
  return (await recentThreads()).find((post) => String(post.text || "").replace(/\s+/g, " ").trim().toLowerCase() === expected);
}

async function createText(text, replyToId = "", autoPublish = true) {
  const params = { media_type: "TEXT", text, reply_control: "everyone" };
  if (replyToId) params.reply_to_id = replyToId;
  if (autoPublish) params.auto_publish_text = "true";
  return graph("me/threads", params, "POST");
}

async function createImage(item) {
  const created = await graph("me/threads", {
    media_type: "IMAGE",
    image_url: assetUrl(item),
    alt_text: item.alt_text,
    text: item.text,
    reply_control: "everyone",
  }, "POST");
  await waitForContainer(created.id);
  return graph("me/threads_publish", { creation_id: created.id }, "POST");
}

async function savePlan(payload) {
  await fs.writeFile(planPath, `${JSON.stringify(payload, null, 2)}\n`);
}

async function recordRoot(payload, item, post, source) {
  item.threads_media_id = post.id;
  item.threads_url = post.permalink || item.threads_url || "";
  item.published_at = post.timestamp || item.published_at || new Date().toISOString();
  item.published_via = source;
  item.published_reply_ids ||= [];
  await savePlan(payload);
}

async function publishReplies(payload, item) {
  let parentId = item.published_reply_ids?.at(-1) || item.threads_media_id;
  const completed = item.published_reply_ids?.length || 0;
  for (let index = completed; index < item.replies.length; index += 1) {
    const created = await createText(item.replies[index], parentId, true);
    const post = await readThread(created.id);
    item.published_reply_ids.push(post.id);
    item.published_reply_urls ||= [];
    item.published_reply_urls.push(post.permalink || "");
    parentId = post.id;
    await savePlan(payload);
  }
}

async function setOutput(values) {
  const lines = Object.entries(values).map(([key, value]) => `${key}=${String(value ?? "").replaceAll("\n", " ")}`);
  if (process.env.GITHUB_OUTPUT) await fs.appendFile(process.env.GITHUB_OUTPUT, `${lines.join("\n")}\n`);
  for (const line of lines) console.log(line);
}

function nowWib() {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Jakarta", dateStyle: "short", timeStyle: "medium", hourCycle: "h23" }).format(now);
}

async function main() {
  const payload = JSON.parse(await fs.readFile(planPath, "utf8"));
  const item = selectItem(payload.items);
  if (mode === "plan") {
    await setOutput({ result: item ? "post_selected" : "no_post_due", post_id: item?.id || "", now_wib: nowWib() });
    return;
  }

  requireConfig(item);
  const profile = await account();

  if (mode === "verify") {
    const next = item || payload.items.find((entry) => entry.status === "queued_auto");
    const asset = next?.media_type === "IMAGE" ? await verifyAsset(assetUrl(next)) : null;
    await setOutput({ result: "verified", username: profile.username, user_id: profile.id, post_id: next?.id || "", media_type: next?.media_type || "", asset_url: asset?.url || "", now_wib: nowWib() });
    return;
  }

  if (mode === "preflight") {
    const next = item || payload.items.find((entry) => entry.status === "queued_auto");
    if (!next) return setOutput({ result: "no_post_due", now_wib: nowWib() });
    if (next.media_type === "IMAGE") await verifyAsset(assetUrl(next));
    const params = next.media_type === "IMAGE"
      ? { media_type: "IMAGE", image_url: assetUrl(next), alt_text: next.alt_text, text: next.text }
      : { media_type: "TEXT", text: next.text };
    const created = await graph("me/threads", params, "POST");
    await waitForContainer(created.id);
    await setOutput({ result: "preflight_ready", username: profile.username, post_id: next.id, container_id: created.id, media_type: next.media_type, now_wib: nowWib() });
    return;
  }

  if (!item) return setOutput({ result: "no_post_due", now_wib: nowWib() });
  if (item.approval_status !== "approved") throw new Error(`${item.id} has not passed approval`);
  if (item.status === "published") return setOutput({ result: "already_recorded", post_id: item.id, threads_url: item.threads_url || "" });

  let rootPost;
  if (item.threads_media_id) {
    rootPost = await readThread(item.threads_media_id);
  } else {
    const existing = await findExisting(item);
    if (existing) {
      rootPost = existing;
      await recordRoot(payload, item, rootPost, "github_actions_reconciled");
    } else if (item.media_type === "IMAGE") {
      await verifyAsset(assetUrl(item));
      const published = await createImage(item);
      rootPost = await readThread(published.id);
      await recordRoot(payload, item, rootPost, "github_actions_threads_api");
    } else {
      const published = await createText(item.text, "", true);
      rootPost = await readThread(published.id);
      await recordRoot(payload, item, rootPost, "github_actions_threads_api");
    }
  }

  await publishReplies(payload, item);
  item.status = "published";
  item.published_at ||= rootPost.timestamp || new Date().toISOString();
  await savePlan(payload);
  await setOutput({ result: "published", post_id: item.id, media_type: item.media_type, replies: item.published_reply_ids?.length || 0, threads_media_id: rootPost.id, threads_url: rootPost.permalink || item.threads_url || "" });
}

main().catch(async (error) => {
  console.error(`threads_publisher_error=${error.message}`);
  await setOutput({ result: "failed", error: error.message });
  process.exitCode = 1;
});
