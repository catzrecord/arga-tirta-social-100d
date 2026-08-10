import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const plan = JSON.parse(await fs.readFile(path.join(root, "content-plan.json"), "utf8"));
if (plan.length !== 100) throw new Error(`Expected 100 posts, received ${plan.length}`);
if (new Set(plan.map((x) => x.id)).size !== 100) throw new Error("Duplicate post IDs");
const hashes = new Map();
let assetCount = 0;
for (const item of plan) {
  if (item.time_wib !== "19:17") throw new Error(`Bad time for ${item.id}`);
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
  const sourceType = item.source_post_type || item.post_type;
  const expected = sourceType === "single" ? 1 : item.content_theme === "text_only" ? 4 : 3;
  if (item.assets.length !== expected || item.slide_count !== expected) {
    throw new Error(`Bad slide count for ${item.id}`);
  }
  if (!item.final_caption?.trim()) throw new Error(`Blank caption ${item.id}`);
  for (const asset of item.assets) {
    const file = path.join(root, "public", asset);
    const bytes = await fs.readFile(file);
    const digest = crypto.createHash("sha256").update(bytes).digest("hex");
    if (hashes.has(digest)) throw new Error(`Exact duplicate: ${asset} and ${hashes.get(digest)}`);
    hashes.set(digest, asset);
    if (bytes.length < 30_000) throw new Error(`Asset suspiciously small: ${asset}`);
    assetCount += 1;
  }
  if (item.post_type === "reel") {
    if (item.source_post_type !== "carousel" || item.audio?.selection !== "trending_western") {
      throw new Error(`Bad Reel source/audio policy ${item.id}`);
    }
    if (item.audio?.graph_api_attachment !== true || !item.audio?.western_audio_key) {
      throw new Error(`Incomplete Graph Audio direction ${item.id}`);
    }
    const reel = await fs.readFile(path.join(root, "public", item.reel_asset));
    if (reel.length < 100_000) throw new Error(`Reel suspiciously small: ${item.reel_asset}`);
  }
}
const singles = plan.filter((x) => x.post_type === "single").length;
const isCarouselSource = (x) => (x.source_post_type || x.post_type) === "carousel";
const photoCarousels = plan.filter((x) => isCarouselSource(x) && x.content_theme !== "text_only").length;
const textCarousels = plan.filter((x) => x.content_theme === "text_only").length;
if (singles !== 57 || photoCarousels !== 29 || textCarousels !== 14 || assetCount !== 200) {
  throw new Error(`Bad mix: ${singles}/${photoCarousels}/${textCarousels}/${assetCount}`);
}
const reels = plan.filter((x) => x.post_type === "reel").length;
console.log(`Validated ${plan.length} posts and ${assetCount} unique source images: ${reels} Reel, ${singles} single, ${photoCarousels} photo-carousel sources, ${textCarousels} text-carousel sources.`);
