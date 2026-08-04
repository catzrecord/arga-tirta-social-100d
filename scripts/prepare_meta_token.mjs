#!/usr/bin/env node

import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const statePath = path.join(root, ".state", "meta-token.enc");
const graphHost = process.env.META_GRAPH_HOST || "graph.instagram.com";
const graphVersion = process.env.META_GRAPH_VERSION || "v25.0";
const fallbackToken = process.env.META_ACCESS_TOKEN || "";
const accountId = process.env.INSTAGRAM_USER_ID || "";
const encryptionKey = decodeKey(process.env.META_TOKEN_ENCRYPTION_KEY || "");
const refreshAfterMs = 25 * 24 * 60 * 60 * 1000;
const aad = Buffer.from("arga-tirta-meta-token:v1", "utf8");

function decodeKey(value) {
  const key = Buffer.from(value, "base64");
  if (key.length !== 32) {
    throw new Error("META_TOKEN_ENCRYPTION_KEY must be a base64-encoded 32-byte key");
  }
  return key;
}

function decryptState(payload) {
  if (payload.version !== 1 || payload.alg !== "A256GCM") {
    throw new Error("Unsupported encrypted Meta token state");
  }
  const decipher = crypto.createDecipheriv(
    "aes-256-gcm",
    encryptionKey,
    Buffer.from(payload.iv, "base64"),
  );
  decipher.setAAD(aad);
  decipher.setAuthTag(Buffer.from(payload.tag, "base64"));
  const plaintext = Buffer.concat([
    decipher.update(Buffer.from(payload.ciphertext, "base64")),
    decipher.final(),
  ]);
  return JSON.parse(plaintext.toString("utf8"));
}

function encryptState(state) {
  const iv = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv("aes-256-gcm", encryptionKey, iv);
  cipher.setAAD(aad);
  const ciphertext = Buffer.concat([
    cipher.update(JSON.stringify(state), "utf8"),
    cipher.final(),
  ]);
  return {
    version: 1,
    alg: "A256GCM",
    iv: iv.toString("base64"),
    tag: cipher.getAuthTag().toString("base64"),
    ciphertext: ciphertext.toString("base64"),
  };
}

async function readState() {
  try {
    return decryptState(JSON.parse(await fs.readFile(statePath, "utf8")));
  } catch (error) {
    if (error?.code === "ENOENT") return null;
    throw error;
  }
}

async function writeState(state) {
  await fs.mkdir(path.dirname(statePath), { recursive: true });
  await fs.writeFile(statePath, `${JSON.stringify(encryptState(state), null, 2)}\n`, {
    mode: 0o600,
  });
}

async function jsonResponse(response) {
  const text = await response.text();
  let payload;
  try {
    payload = text ? JSON.parse(text) : {};
  } catch {
    payload = { raw: text.slice(0, 300) };
  }
  if (!response.ok || payload.error) {
    const message = payload.error?.message || payload.message || `HTTP ${response.status}`;
    throw new Error(message);
  }
  return payload;
}

async function refreshToken(token) {
  const url = new URL(`https://${graphHost}/refresh_access_token`);
  url.searchParams.set("grant_type", "ig_refresh_token");
  url.searchParams.set("access_token", token);
  return jsonResponse(await fetch(url, { headers: { accept: "application/json" } }));
}

async function verifyToken(token) {
  const url = new URL(`https://${graphHost}/${graphVersion}/${accountId}`);
  url.searchParams.set("fields", "id,username,account_type");
  url.searchParams.set("access_token", token);
  const account = await jsonResponse(await fetch(url, { headers: { accept: "application/json" } }));
  if (String(account.id) !== String(accountId)) {
    throw new Error(`Instagram token resolved to unexpected account ${account.id || "unknown"}`);
  }
  const expectedUsername = process.env.EXPECTED_INSTAGRAM_USERNAME || "";
  if (expectedUsername && account.username !== expectedUsername) {
    throw new Error(`Instagram token resolved to unexpected username ${account.username || "unknown"}`);
  }
  return account;
}

async function appendOutput(values) {
  if (!process.env.GITHUB_OUTPUT) return;
  const lines = Object.entries(values).map(([key, value]) => `${key}=${String(value)}`);
  await fs.appendFile(process.env.GITHUB_OUTPUT, `${lines.join("\n")}\n`);
}

async function exposeTokenToLaterSteps(token) {
  if (!process.env.GITHUB_ENV) throw new Error("GITHUB_ENV is required");
  if (process.env.GITHUB_ACTIONS === "true") {
    process.stdout.write(`::add-mask::${token}\n`);
  }
  await fs.appendFile(process.env.GITHUB_ENV, `META_ACCESS_TOKEN=${token}\n`);
}

async function main() {
  if (!accountId) throw new Error("INSTAGRAM_USER_ID is required");
  const stored = await readState();
  let token = stored?.access_token || fallbackToken;
  if (!token) throw new Error("META_ACCESS_TOKEN is required for initial token state");

  const refreshedAt = stored?.refreshed_at ? Date.parse(stored.refreshed_at) : 0;
  const forceRefresh = process.env.META_TOKEN_FORCE_REFRESH === "true";
  const refreshDue =
    forceRefresh || !Number.isFinite(refreshedAt) || Date.now() - refreshedAt >= refreshAfterMs;
  let stateChanged = false;
  let refreshStatus = "reused";
  let expiresIn = Number(stored?.expires_in || 0);

  if (!stored || refreshDue) {
    const refreshed = await refreshToken(token);
    if (!refreshed.access_token) throw new Error("Meta token refresh returned no access token");
    token = refreshed.access_token;
    expiresIn = Number(refreshed.expires_in || 0);
    await writeState({
      access_token: token,
      refreshed_at: new Date().toISOString(),
      expires_in: expiresIn,
      permissions: refreshed.permissions || "",
    });
    stateChanged = true;
    refreshStatus = "refreshed";
  }

  const account = await verifyToken(token);
  await exposeTokenToLaterSteps(token);
  await appendOutput({
    state_changed: stateChanged,
    refresh_status: refreshStatus,
    expires_in_days: expiresIn ? Math.floor(expiresIn / 86400) : "",
    username: account.username,
  });
  console.log(`refresh_status=${refreshStatus}`);
  console.log(`username=${account.username}`);
  if (expiresIn) console.log(`expires_in_days=${Math.floor(expiresIn / 86400)}`);
}

main().catch((error) => {
  console.error(`token_prepare_error=${error.message}`);
  process.exitCode = 1;
});

