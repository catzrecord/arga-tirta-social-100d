import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const plan = JSON.parse(await fs.readFile(path.join(root, "content-plan.json"), "utf8"));
const expectedPosts = 184;
if (plan.length !== expectedPosts) throw new Error(`Expected ${expectedPosts} posts, received ${plan.length}`);
if (new Set(plan.map((x) => x.id)).size !== expectedPosts) throw new Error("Duplicate post IDs");
if (new Set(plan.map((x) => x.date)).size !== expectedPosts) throw new Error("Duplicate post dates");
if (plan[0]?.date !== "2026-08-24" || plan.at(-1)?.date !== "2027-02-23") {
  throw new Error(`Bad campaign range: ${plan[0]?.date} to ${plan.at(-1)?.date}`);
}

const hashes = new Map();
let imageCount = 0;
let videoCount = 0;
for (const item of plan) {
  if (item.time_wib !== "19:17") throw new Error(`Bad time for ${item.id}`);
  if (Number(item.id) < 1001 || Number(item.id) > 1184) throw new Error(`Bad campaign ID ${item.id}`);
  const validStatus = item.status === "queued_auto" || item.status === "published";
  if (!validStatus || item.approval_status !== "approved") {
    throw new Error(`Post ${item.id} is not approved or in a valid queue state`);
  }
  if (item.status === "published" && !item.instagram_media_id) {
    throw new Error(`Published post ${item.id} has no Instagram media ID`);
  }
  if (!["single", "carousel", "reel"].includes(item.post_type)) {
    throw new Error(`Bad post type ${item.id}: ${item.post_type}`);
  }
  const expectedAssets = item.post_type === "carousel" ? 4 : 1;
  if (!Array.isArray(item.assets) || item.assets.length !== expectedAssets || item.slide_count !== expectedAssets) {
    throw new Error(`Bad asset count for ${item.id}`);
  }
  if (!item.final_caption?.trim()) throw new Error(`Blank caption ${item.id}`);
  if (item.visual_revision !== "digital-imaging-cast-shadow-v2") {
    throw new Error(`Old visual revision remains on ${item.id}`);
  }
  for (const asset of item.assets) {
    if (!asset.startsWith("posts/arga-tirta-6m-v2/")) throw new Error(`Old asset path remains: ${asset}`);
    const file = path.join(root, "public", asset);
    const bytes = await fs.readFile(file);
    const digest = crypto.createHash("sha256").update(bytes).digest("hex");
    if (hashes.has(digest)) throw new Error(`Exact duplicate: ${asset} and ${hashes.get(digest)}`);
    hashes.set(digest, asset);
    if (bytes.length < 45_000) throw new Error(`Asset suspiciously small: ${asset}`);
    imageCount += 1;
  }
  if (item.post_type === "reel") {
    if (!item.reel_asset?.startsWith("posts/arga-tirta-6m-v2/")) throw new Error(`Bad Reel path ${item.id}`);
    if (item.audio?.selection !== "trending_western" || item.audio?.graph_api_attachment !== true) {
      throw new Error(`Incomplete Reel audio direction ${item.id}`);
    }
    if (!item.audio?.western_audio_key || !Array.isArray(item.audio?.western_candidates)) {
      throw new Error(`Incomplete Western audio candidates ${item.id}`);
    }
    const reel = await fs.readFile(path.join(root, "public", item.reel_asset));
    if (reel.length < 250_000) throw new Error(`Reel suspiciously small: ${item.reel_asset}`);
    videoCount += 1;
  }
}

const counts = Object.fromEntries(["single", "carousel", "reel"].map((type) => [type, plan.filter((x) => x.post_type === type).length]));
if (counts.single !== 53 || counts.carousel !== 79 || counts.reel !== 52) {
  throw new Error(`Bad weekly mix: ${JSON.stringify(counts)}`);
}
if (imageCount !== 421 || videoCount !== 52) {
  throw new Error(`Bad media totals: ${imageCount} images / ${videoCount} videos`);
}
console.log(`Validated ${plan.length} approved posts: ${counts.carousel} carousel, ${counts.single} single, ${counts.reel} Reel; ${imageCount} unique images and ${videoCount} videos.`);
