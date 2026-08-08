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
  const expected = item.post_type === "single" ? 1 : item.content_theme === "text_only" ? 4 : 3;
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
}
const singles = plan.filter((x) => x.post_type === "single").length;
const photoCarousels = plan.filter((x) => x.post_type === "carousel" && x.content_theme !== "text_only").length;
const textCarousels = plan.filter((x) => x.content_theme === "text_only").length;
if (singles !== 57 || photoCarousels !== 29 || textCarousels !== 14 || assetCount !== 200) {
  throw new Error(`Bad mix: ${singles}/${photoCarousels}/${textCarousels}/${assetCount}`);
}
console.log(`Validated ${plan.length} posts and ${assetCount} unique assets: ${singles} single, ${photoCarousels} photo carousel, ${textCarousels} text-only carousel.`);
