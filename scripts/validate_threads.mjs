#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const planPath = path.join(root, "threads-content-plan.json");

function fail(message) {
  throw new Error(`Threads queue validation: ${message}`);
}

function dueAt(item) {
  return new Date(`${item.date}T${item.time_wib}:00+07:00`);
}

async function main() {
  const payload = JSON.parse(await fs.readFile(planPath, "utf8"));
  const items = payload.items;
  if (!Array.isArray(items) || items.length !== 200) fail(`expected 200 starters, got ${items?.length}`);
  if (payload.timezone !== "Asia/Jakarta") fail("timezone must be Asia/Jakarta");

  const ids = new Set();
  let photoPosts = 0;
  let threadSessions = 0;
  let replyPosts = 0;
  let ctaPosts = 0;
  const byDay = new Map();

  for (const item of items) {
    if (!/^AT-THR-D\d{3}-(AM|PM)$/.test(item.id || "")) fail(`bad ID ${item.id}`);
    if (ids.has(item.id)) fail(`duplicate ID ${item.id}`);
    ids.add(item.id);
    if (!Number.isInteger(item.day) || item.day < 1 || item.day > 100) fail(`${item.id} has invalid day`);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(item.date || "")) fail(`${item.id} has invalid date`);
    if (!/^(08:17|19:17)$/.test(item.time_wib || "")) fail(`${item.id} has invalid WIB time`);
    if (Number.isNaN(dueAt(item).valueOf())) fail(`${item.id} has invalid scheduled time`);
    if (item.approval_status !== "approved") fail(`${item.id} is not approved`);
    if (!["queued_auto", "published"].includes(item.status)) fail(`${item.id} has invalid status`);
    if (!["TEXT", "IMAGE"].includes(item.media_type)) fail(`${item.id} has invalid media type`);
    if (typeof item.text !== "string" || item.text.length < 80 || item.text.length > 500) {
      fail(`${item.id} text length is ${item.text?.length}`);
    }
    if (!Array.isArray(item.replies)) fail(`${item.id} replies must be an array`);
    for (const [index, reply] of item.replies.entries()) {
      if (typeof reply !== "string" || reply.length < 60 || reply.length > 500) {
        fail(`${item.id} reply ${index + 1} length is ${reply?.length}`);
      }
    }
    if (item.format === "mini_thread") {
      threadSessions += 1;
      if (item.replies.length < 3 || item.replies.length > 4) fail(`${item.id} must have 3-4 replies`);
    } else if (item.replies.length) {
      fail(`${item.id} is standalone but has replies`);
    }
    replyPosts += item.replies.length;
    if (item.cta_type !== "conversation") ctaPosts += 1;

    if (item.media_type === "IMAGE") {
      photoPosts += 1;
      if (!item.asset_original) fail(`${item.id} image is not marked original`);
      if (!item.asset || !item.alt_text) fail(`${item.id} is missing asset metadata`);
      const assetPath = path.resolve(root, "public", item.asset);
      if (!assetPath.startsWith(path.resolve(root, "public") + path.sep)) fail(`${item.id} asset escapes public`);
      const stat = await fs.stat(assetPath);
      if (!stat.isFile() || stat.size < 20_000) fail(`${item.id} asset is missing or too small`);
    }

    const dayItems = byDay.get(item.day) || [];
    dayItems.push(item);
    byDay.set(item.day, dayItems);
  }

  for (let day = 1; day <= 100; day += 1) {
    const dayItems = byDay.get(day) || [];
    if (dayItems.length !== 2) fail(`day ${day} must have exactly two starters`);
    const sessions = dayItems.map((item) => item.session).sort().join(",");
    if (sessions !== "AM,PM") fail(`day ${day} must contain AM and PM`);
  }
  if (photoPosts !== 28) fail(`expected 28 real-photo posts, got ${photoPosts}`);
  if (threadSessions !== 28) fail(`expected 28 mini-thread sessions, got ${threadSessions}`);
  if (replyPosts !== 84) fail(`expected 84 reply posts, got ${replyPosts}`);
  if (ctaPosts !== 71) fail(`expected 71 CTA posts, got ${ctaPosts}`);

  console.log(JSON.stringify({ result: "valid", starters: items.length, reply_posts: replyPosts, total_publications: items.length + replyPosts, photo_posts: photoPosts, thread_sessions: threadSessions, cta_posts: ctaPosts }, null, 2));
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
