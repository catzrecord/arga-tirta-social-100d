#!/usr/bin/env node

import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const statePath = path.join(root, ".state", "threads-token.enc");
const graphBase = (process.env.THREADS_GRAPH_BASE || "https://graph.threads.net").replace(/\/+$/, "");
const fallbackToken = process.env.THREADS_ACCESS_TOKEN || "";
const expectedUsername = process.env.THREADS_EXPECTED_USERNAME || "cv.argatirta";
const key = decodeKey(process.env.META_TOKEN_ENCRYPTION_KEY || "");
const refreshAfterMs = 25 * 24 * 60 * 60 * 1000;
const aad = Buffer.from("arga-tirta-threads-token:v1", "utf8");

function decodeKey(value) {
  const decoded = Buffer.from(value, "base64");
  if (decoded.length !== 32) throw new Error("META_TOKEN_ENCRYPTION_KEY must be a base64-encoded 32-byte key");
  return decoded;
}

function decrypt(payload) {
  if (payload.version !== 1 || payload.alg !== "A256GCM") throw new Error("Unsupported encrypted Threads token state");
  const decipher = crypto.createDecipheriv("aes-256-gcm", key, Buffer.from(payload.iv, "base64"));
  decipher.setAAD(aad);
  decipher.setAuthTag(Buffer.from(payload.tag, "base64"));
  const plain = Buffer.concat([decipher.update(Buffer.from(payload.ciphertext, "base64")), decipher.final()]);
  return JSON.parse(plain.toString("utf8"));
}

function encrypt(state) {
  const iv = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv("aes-256-gcm", key, iv);
  cipher.setAAD(aad);
  const ciphertext = Buffer.concat([cipher.update(JSON.stringify(state), "utf8"), cipher.final()]);
  return { version: 1, alg: "A256GCM", iv: iv.toString("base64"), tag: cipher.getAuthTag().toString("base64"), ciphertext: ciphertext.toString("base64") };
}

async function readState() {
  try {
    return decrypt(JSON.parse(await fs.readFile(statePath, "utf8")));
  } catch (error) {
    if (error?.code === "ENOENT") return null;
    throw error;
  }
}

async function writeState(state) {
  await fs.mkdir(path.dirname(statePath), { recursive: true });
  await fs.writeFile(statePath, `${JSON.stringify(encrypt(state), null, 2)}\n`, { mode: 0o600 });
}

async function jsonResponse(response) {
  const text = await response.text();
  let payload = {};
  try { payload = text ? JSON.parse(text) : {}; } catch { payload = { raw: text.slice(0, 300) }; }
  if (!response.ok || payload.error) throw new Error(payload.error?.message || payload.message || `HTTP ${response.status}`);
  return payload;
}

async function refreshToken(token) {
  const url = new URL(`${graphBase}/refresh_access_token`);
  url.searchParams.set("grant_type", "th_refresh_token");
  url.searchParams.set("access_token", token);
  return jsonResponse(await fetch(url, { headers: { accept: "application/json" } }));
}

async function verifyToken(token) {
  const url = new URL(`${graphBase}/me`);
  url.searchParams.set("fields", "id,username,name");
  url.searchParams.set("access_token", token);
  const profile = await jsonResponse(await fetch(url, { headers: { accept: "application/json" } }));
  if (expectedUsername && profile.username !== expectedUsername) throw new Error(`Threads token resolved to @${profile.username || "unknown"}, expected @${expectedUsername}`);
  return profile;
}

async function expose(token) {
  if (!process.env.GITHUB_ENV) return;
  if (process.env.GITHUB_ACTIONS === "true") process.stdout.write(`::add-mask::${token}\n`);
  await fs.appendFile(process.env.GITHUB_ENV, `THREADS_ACCESS_TOKEN=${token}\n`);
}

async function output(values) {
  if (!process.env.GITHUB_OUTPUT) return;
  await fs.appendFile(process.env.GITHUB_OUTPUT, Object.entries(values).map(([keyName, value]) => `${keyName}=${value}`).join("\n") + "\n");
}

async function main() {
  const stored = await readState();
  let token = stored?.access_token || fallbackToken;
  if (!token) throw new Error("THREADS_ACCESS_TOKEN is required for initial token state");

  const refreshedAt = stored?.refreshed_at ? Date.parse(stored.refreshed_at) : 0;
  const force = process.env.THREADS_TOKEN_FORCE_REFRESH === "true";
  const due = force || !Number.isFinite(refreshedAt) || Date.now() - refreshedAt >= refreshAfterMs;
  let stateChanged = false;
  let status = "reused";
  let expiresIn = Number(stored?.expires_in || 0);

  if (!stored || due) {
    const refreshed = await refreshToken(token);
    token = refreshed.access_token || token;
    expiresIn = Number(refreshed.expires_in || expiresIn || 0);
    await writeState({ access_token: token, refreshed_at: new Date().toISOString(), expires_in: expiresIn });
    stateChanged = true;
    status = "refreshed";
  }

  const profile = await verifyToken(token);
  await expose(token);
  await output({ state_changed: stateChanged, refresh_status: status, expires_in_days: expiresIn ? Math.floor(expiresIn / 86400) : "", username: profile.username, user_id: profile.id });
  console.log(`refresh_status=${status}`);
  console.log(`username=${profile.username}`);
  console.log(`user_id=${profile.id}`);
}

main().catch((error) => {
  console.error(`threads_token_prepare_error=${error.message}`);
  process.exitCode = 1;
});
