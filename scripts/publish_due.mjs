#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const planPath = path.join(root, "content-plan.json");
const graphVersion = process.env.META_GRAPH_VERSION || "v25.0";
const graphHost = process.env.META_GRAPH_HOST || "graph.instagram.com";
const graphBase = `https://${graphHost}/${graphVersion}`;
const accountId = process.env.INSTAGRAM_USER_ID;
const accessToken = process.env.META_ACCESS_TOKEN;
const audioGraphHost = process.env.META_AUDIO_GRAPH_HOST || "graph.facebook.com";
const audioGraphBase = `https://${audioGraphHost}/${graphVersion}`;
const audioAccountId = process.env.META_AUDIO_INSTAGRAM_USER_ID || accountId;
const audioAccessToken = process.env.META_AUDIO_ACCESS_TOKEN;
const assetBase = (process.env.PUBLIC_ASSET_BASE_URL || "").replace(/\/+$/, "");
const mode = argument("mode") || process.env.ARGA_TIRTA_PUBLISH_MODE || "due";
const requestedId = Number(argument("post-id") || process.env.ARGA_TIRTA_POST_ID || 0);
const now = new Date(process.env.ARGA_TIRTA_NOW || Date.now());

function argument(name) {
  const exact = `--${name}`;
  const prefix = `${exact}=`;
  const index = process.argv.indexOf(exact);
  if (index >= 0) return process.argv[index + 1];
  const inline = process.argv.find((value) => value.startsWith(prefix));
  return inline?.slice(prefix.length);
}

function requireConfiguration() {
  const missing = [];
  if (!accountId) missing.push("INSTAGRAM_USER_ID");
  if (!accessToken) missing.push("META_ACCESS_TOKEN");
  if (!assetBase) missing.push("PUBLIC_ASSET_BASE_URL");
  if (missing.length) throw new Error(`Missing configuration: ${missing.join(", ")}`);
}

function jakartaParts(date) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Jakarta",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
  }).formatToParts(date);
  return Object.fromEntries(parts.map((part) => [part.type, part.value]));
}

function dueAt(item) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(item.date || "")) return null;
  if (!/^\d{2}:\d{2}$/.test(item.time_wib || "")) return null;
  return new Date(`${item.date}T${item.time_wib}:00+07:00`);
}

function selectItem(plan) {
  if (requestedId) {
    const item = plan.find((entry) => Number(entry.id) === requestedId);
    if (!item) throw new Error(`Post ${requestedId} was not found`);
    return item;
  }
  const candidates = plan
    .filter((item) => item.status === "queued_auto" && item.approval_status === "approved")
    .map((item) => ({ item, due: dueAt(item) }))
    .filter(({ due }) => due && due <= now)
    .sort((a, b) => a.due - b.due || a.item.id - b.item.id);
  return candidates[0]?.item;
}

function requireApproved(item) {
  if (item.status !== "published" && item.approval_status !== "approved") {
    throw new Error(`Post ${item.id} has not passed editorial approval`);
  }
}

function assetUrl(item, asset) {
  const relative = String(asset || "").replace(/^\/+/, "");
  if (!relative) throw new Error(`Post ${item.id} has no asset path`);
  const url = new URL(`${assetBase}/${relative}`);
  const version = String(item.asset_version || item.visual_revision || "").trim();
  if (version) url.searchParams.set("v", version);
  return url.toString();
}

function assetUrls(item) {
  const assets = Array.isArray(item.assets) && item.assets.length ? item.assets : [item.asset];
  return assets.map((asset) => assetUrl(item, asset));
}

function publishAssetUrls(item) {
  if (item.post_type === "reel") return [assetUrl(item, item.reel_asset)];
  return assetUrls(item);
}

function altText(item, slideIndex = 0) {
  const title = String(item.title || "Arga Tirta field note").replace(/\s+/g, " ").trim();
  const slide =
    item.post_type === "carousel"
      ? ` Slide ${slideIndex + 1} of ${item.slide_count || item.assets?.length || 1}.`
      : "";
  return `${title}.${slide} Arga Tirta social queue item ${String(item.id).padStart(3, "0")}.`;
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
    const message =
      payload.error?.error_user_msg ||
      payload.error?.message ||
      payload.message ||
      `HTTP ${response.status}`;
    const code = payload.error?.code ? ` [code ${payload.error.code}]` : "";
    throw new Error(`${message}${code}`);
  }
  return payload;
}

async function graph(pathname, params = {}, method = "GET") {
  const url = new URL(`${graphBase}/${pathname.replace(/^\/+/, "")}`);
  const body = new URLSearchParams({ ...params, access_token: accessToken });
  if (method === "GET") {
    for (const [key, value] of body) url.searchParams.set(key, value);
    return responseJson(await fetch(url, { headers: { accept: "application/json" } }));
  }
  return responseJson(
    await fetch(url, {
      method,
      headers: {
        accept: "application/json",
        "content-type": "application/x-www-form-urlencoded",
      },
      body,
    }),
  );
}

async function audioGraph(pathname, params = {}, method = "GET") {
  if (!audioAccessToken) {
    throw new Error("META_AUDIO_ACCESS_TOKEN is required for Western trending Reel audio");
  }
  const url = new URL(`${audioGraphBase}/${pathname.replace(/^\/+/, "")}`);
  const body = new URLSearchParams({ ...params, access_token: audioAccessToken });
  if (method === "GET") {
    for (const [key, value] of body) url.searchParams.set(key, value);
    return responseJson(await fetch(url, { headers: { accept: "application/json" } }));
  }
  return responseJson(await fetch(url, {
    method,
    headers: { accept: "application/json", "content-type": "application/x-www-form-urlencoded" },
    body,
  }));
}

async function verifyAsset(url, expectedType = "image") {
  const response = await fetch(url, { method: "HEAD", redirect: "follow" });
  if (!response.ok) throw new Error(`Asset returned HTTP ${response.status}: ${url}`);
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.startsWith(`${expectedType}/`)) {
    throw new Error(`Asset is not ${expectedType} (${contentType || "missing content-type"}): ${url}`);
  }
  return {
    url: response.url,
    contentType,
    contentLength: Number(response.headers.get("content-length") || 0),
  };
}

function normalizeAudio(value) {
  return String(value || "").normalize("NFKD").replace(/[^a-z0-9]+/gi, " ").trim().toLowerCase();
}

async function loadWesternAudioCatalog() {
  const payload = JSON.parse(await fs.readFile(path.join(root, "trending-western-audio.json"), "utf8"));
  return payload.tracks || [];
}

function exactCatalogMatch(audio, track) {
  const title = normalizeAudio(audio.title);
  const artist = normalizeAudio(audio.display_artist);
  return title === normalizeAudio(track.title) && artist.includes(normalizeAudio(track.artist));
}

async function selectWesternTrendingAudio(item) {
  if (item.post_type !== "reel") return null;
  if (!audioAccessToken || !audioAccountId) return null;
  const catalog = await loadWesternAudioCatalog();
  const byKey = new Map(catalog.map((track) => [track.key, track]));
  const orderedKeys = [item.audio?.western_audio_key, ...(item.audio?.western_candidates || [])].filter(Boolean);
  const ordered = [...new Set(orderedKeys)].map((key) => byKey.get(key)).filter(Boolean);
  if (!ordered.length) throw new Error(`Reel ${item.id} has no approved Western audio candidates`);

  const trending = await audioGraph("ig_audio", {
    audio_type: "music",
    user_id: audioAccountId,
  });
  for (const track of ordered) {
    const match = (trending.audio || []).find((audio) => exactCatalogMatch(audio, track));
    if (match) return { ...match, selection: "trending_default", catalog_key: track.key };
  }

  throw new Error(`No approved Western music appears in the current Instagram trending list for Reel ${item.id}`);
}

async function verifyAccount() {
  return graph(`${accountId}?fields=id,username,account_type,media_count`);
}

async function recentMedia() {
  try {
    const payload = await graph(
      `${accountId}/media?fields=id,caption,permalink,timestamp,alt_text&limit=100`,
    );
    return payload.data || [];
  } catch (error) {
    if (!/alt_text|field/i.test(error.message)) throw error;
    const payload = await graph(
      `${accountId}/media?fields=id,caption,permalink,timestamp&limit=100`,
    );
    return payload.data || [];
  }
}

async function findExisting(item) {
  const marker = `queue item ${String(item.id).padStart(3, "0")}`;
  const expectedCaption = String(item.final_caption || "").replace(/\s+/g, " ").trim().toLowerCase();
  const media = await recentMedia();
  return media.find((entry) => {
    if (String(entry.alt_text || "").toLowerCase().includes(marker)) return true;
    const caption = String(entry.caption || "").replace(/\s+/g, " ").trim().toLowerCase();
    return expectedCaption && caption === expectedCaption;
  });
}

function captionParams(item) {
  const params = {};
  const caption = String(item.final_caption || "").trim();
  if (caption) params.caption = caption;
  if (process.env.META_DISCLOSE_AI !== "false") params.is_ai_generated = "true";
  return params;
}

async function createImageContainer(item, imageUrl, slideIndex = 0, isCarouselItem = false) {
  const params = {
    image_url: imageUrl,
    alt_text: altText(item, slideIndex),
  };
  if (isCarouselItem) params.is_carousel_item = "true";
  else Object.assign(params, captionParams(item));

  try {
    return await graph(`${accountId}/media`, params, "POST");
  } catch (error) {
    if (!/is_ai_generated|parameter/i.test(error.message) || !params.is_ai_generated) throw error;
    delete params.is_ai_generated;
    return graph(`${accountId}/media`, params, "POST");
  }
}

async function createReelContainer(item, videoUrl, audio) {
  const params = {
    media_type: "REELS",
    video_url: videoUrl,
    share_to_feed: "true",
    ...captionParams(item),
  };
  if (audio) {
    params.audio_configuration = JSON.stringify({
      audio_id: audio.audio_id,
      audio_volume: Number(item.audio?.audio_volume ?? 100),
      video_volume: Number(item.audio?.video_volume ?? 0),
    });
  }
  const create = () => audio
    ? audioGraph(`${audioAccountId}/media`, params, "POST")
    : graph(`${accountId}/media`, params, "POST");
  try {
    return await create();
  } catch (error) {
    if (!/is_ai_generated|parameter/i.test(error.message) || !params.is_ai_generated) throw error;
    delete params.is_ai_generated;
    return create();
  }
}

async function createContainer(item, imageUrls, audio = null) {
  if (item.post_type === "reel") return createReelContainer(item, imageUrls[0], audio);
  if (item.post_type !== "carousel") {
    return createImageContainer(item, imageUrls[0]);
  }
  if (imageUrls.length < 2 || imageUrls.length > 10) {
    throw new Error(`Carousel ${item.id} must contain 2-10 assets`);
  }

  const children = [];
  for (const [slideIndex, imageUrl] of imageUrls.entries()) {
    const child = await createImageContainer(item, imageUrl, slideIndex, true);
    await waitForContainer(child.id);
    children.push(child.id);
  }

  const params = {
    media_type: "CAROUSEL",
    children: children.join(","),
    ...captionParams(item),
  };
  try {
    return await graph(`${accountId}/media`, params, "POST");
  } catch (error) {
    if (!/is_ai_generated|parameter/i.test(error.message) || !params.is_ai_generated) throw error;
    delete params.is_ai_generated;
    return graph(`${accountId}/media`, params, "POST");
  }
}

async function waitForContainer(containerId, viaAudioApi = false) {
  const deadline = Date.now() + 120_000;
  while (Date.now() < deadline) {
    const status = viaAudioApi
      ? await audioGraph(`${containerId}?fields=status_code,status`)
      : await graph(`${containerId}?fields=status_code,status`);
    if (status.status_code === "FINISHED") return status;
    if (status.status_code === "ERROR" || status.status_code === "EXPIRED") {
      throw new Error(`Meta media container ${status.status_code}: ${status.status || "unknown"}`);
    }
    await new Promise((resolve) => setTimeout(resolve, 5000));
  }
  throw new Error("Timed out waiting for the Meta media container");
}

async function updatePlan(plan, item, media, state, audio = null) {
  const target = plan.find((entry) => Number(entry.id) === Number(item.id));
  target.status = "published";
  target.instagram_media_id = media.id;
  if (media.permalink) target.instagram_url = media.permalink;
  target.published_at = media.timestamp || new Date().toISOString();
  target.published_via = state;
  if (audio) {
    target.published_audio = {
      audio_id: audio.audio_id,
      title: audio.title,
      artist: audio.display_artist,
      selection: audio.selection,
      catalog_key: audio.catalog_key,
    };
  }
  await fs.writeFile(planPath, `${JSON.stringify(plan, null, 2)}\n`);
}

async function setOutput(values) {
  const lines = Object.entries(values).map(([key, value]) => {
    const text = typeof value === "string" ? value : JSON.stringify(value);
    return `${key}=${text.replaceAll("\n", " ")}`;
  });
  if (process.env.GITHUB_OUTPUT) {
    await fs.appendFile(process.env.GITHUB_OUTPUT, `${lines.join("\n")}\n`);
  }
  for (const line of lines) console.log(line);
}

async function main() {
  const plan = JSON.parse(await fs.readFile(planPath, "utf8"));
  const item = selectItem(plan);
  const stamp = jakartaParts(now);
  const currentWib = `${stamp.year}-${stamp.month}-${stamp.day} ${stamp.hour}:${stamp.minute}:${stamp.second} WIB`;

  if (mode === "plan") {
    await setOutput({
      result: item ? "post_selected" : "no_post_due",
      post_id: item?.id || "",
      now_wib: currentWib,
    });
    return;
  }

  requireConfiguration();
  const account = await verifyAccount();

  if (mode === "verify") {
    const next = item || plan.find((entry) => entry.status === "queued_auto");
    const urls = next ? publishAssetUrls(next) : [];
    const expectedType = next?.post_type === "reel" ? "video" : "image";
    const assets = await Promise.all(urls.map((url) => verifyAsset(url, expectedType)));
    await setOutput({
      result: "verified",
      username: account.username || "",
      account_type: account.account_type || "",
      media_count: account.media_count ?? "",
      post_id: next?.id || "",
      post_type: next?.post_type || "",
      asset_count: assets.length,
      asset_url: assets[0]?.url || "",
      now_wib: currentWib,
    });
    return;
  }

  if (mode === "audio-check") {
    const next = item?.post_type === "reel"
      ? item
      : plan.find((entry) => entry.status === "queued_auto" && entry.post_type === "reel");
    if (!next) {
      await setOutput({ result: "no_reel_queued", now_wib: currentWib });
      return;
    }
    const audio = await selectWesternTrendingAudio(next);
    if (!audio) {
      await setOutput({ result: "audio_api_not_configured", post_id: next.id, now_wib: currentWib });
      return;
    }
    await setOutput({
      result: "western_audio_verified",
      username: account.username || "",
      post_id: next.id,
      audio_title: audio.title || "",
      audio_artist: audio.display_artist || "",
      audio_selection: audio.selection,
      now_wib: currentWib,
    });
    return;
  }

  if (mode === "deploy") {
    const next = item || plan.find((entry) => entry.status === "queued_auto");
    await setOutput({
      result: "deploy_ready",
      username: account.username || "",
      account_type: account.account_type || "",
      post_id: next?.id || "",
      post_type: next?.post_type || "",
      asset_count: next ? publishAssetUrls(next).length : 0,
      asset_url: next ? publishAssetUrls(next)[0] : "",
      now_wib: currentWib,
    });
    return;
  }

  if (mode === "preflight") {
    const next = item || plan.find((entry) => entry.status === "queued_auto");
    if (!next) {
      await setOutput({ result: "no_post_due", now_wib: currentWib });
      return;
    }
    requireApproved(next);
    const imageUrls = publishAssetUrls(next);
    const expectedType = next.post_type === "reel" ? "video" : "image";
    await Promise.all(imageUrls.map((url) => verifyAsset(url, expectedType)));
    const audio = await selectWesternTrendingAudio(next);
    const container = await createContainer(next, imageUrls, audio);
    await waitForContainer(container.id, Boolean(audio));
    await setOutput({
      result: "preflight_ready",
      username: account.username || "",
      account_type: account.account_type || "",
      post_id: next.id,
      post_type: next.post_type || "single",
      asset_count: imageUrls.length,
      container_id: container.id,
      asset_url: imageUrls[0],
      now_wib: currentWib,
    });
    return;
  }

  if (!item) {
    await setOutput({ result: "no_post_due", now_wib: currentWib });
    return;
  }
  requireApproved(item);
  if (item.status === "published") {
    await setOutput({
      result: "already_recorded",
      post_id: item.id,
      instagram_url: item.instagram_url || "",
    });
    return;
  }

  const imageUrls = publishAssetUrls(item);
  const expectedType = item.post_type === "reel" ? "video" : "image";
  await Promise.all(imageUrls.map((url) => verifyAsset(url, expectedType)));
  const existing = await findExisting(item);
  if (existing) {
    await updatePlan(plan, item, existing, "github_actions_reconciled");
    await setOutput({
      result: "already_published",
      post_id: item.id,
      instagram_url: existing.permalink || "",
    });
    return;
  }

  const audio = await selectWesternTrendingAudio(item);
  const container = await createContainer(item, imageUrls, audio);
  await waitForContainer(container.id, Boolean(audio));
  const published = item.post_type === "reel" && audio
    ? await audioGraph(`${audioAccountId}/media_publish`, { creation_id: container.id }, "POST")
    : await graph(`${accountId}/media_publish`, { creation_id: container.id }, "POST");
  const media = item.post_type === "reel" && audio
    ? await audioGraph(`${published.id}?fields=id,permalink,timestamp`)
    : await graph(`${published.id}?fields=id,permalink,timestamp`);
  await updatePlan(plan, item, media, "github_actions_graph_api", audio);
  await setOutput({
    result: "published",
    post_id: item.id,
    post_type: item.post_type || "single",
    asset_count: imageUrls.length,
    instagram_media_id: media.id,
    instagram_url: media.permalink || "",
    audio_title: audio?.title || "",
    audio_artist: audio?.display_artist || "",
  });
}

main().catch(async (error) => {
  console.error(`publisher_error=${error.message}`);
  await setOutput({ result: "failed", error: error.message });
  process.exitCode = 1;
});
