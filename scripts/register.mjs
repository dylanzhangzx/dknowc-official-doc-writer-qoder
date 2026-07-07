#!/usr/bin/env node
// 国内 MaaS headless 注册助手（供 Qoder Public skill 调用；纯 node，内置 fetch，无三方依赖）。
//   node register.mjs [--base URL] send     --phone <p>
//   node register.mjs [--base URL] register --phone <p> --vcode <c> [--type 6] [--organ ..] [--name ..] [--channel ..] [--password ..] [--config ../config.ini]
// 无需 cookie / 加密 / 登录态。默认打生产，--base 可切测试环境。

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const DEFAULT_BASE = "https://platform.dknowc.cn/auth/home/userAuto";
const DEFAULT_CHANNEL = "5DBF147C-A4D0-4C3E-AB1A-6C6F5EA39B18";
const DEFAULT_TYPE = "6";
const FALLBACK_REGISTER_URL = `https://platform.dknowc.cn/auth/#/register?channel=${DEFAULT_CHANNEL}&type=${DEFAULT_TYPE}`;
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SKILL_ROOT = path.resolve(__dirname, "..");
const DEFAULT_CONFIG_PATH = path.join(SKILL_ROOT, "config.ini");

function parseArgs(argv) {
  const out = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next === undefined || next.startsWith("--")) { out[key] = true; }
      else { out[key] = next; i++; }
    } else { out._.push(a); }
  }
  return out;
}

async function post(url, payload) {
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), 30000);
  try {
    const r = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: ctl.signal,
    });
    const text = await r.text();
    try { return JSON.parse(text); }
    catch { return { status: false, msg: "非JSON响应(前200字符): " + text.slice(0, 200) }; }
  } catch (e) {
    return { status: false, msg: "请求异常: " + (e && e.message ? e.message : String(e)) };
  } finally { clearTimeout(timer); }
}

function genPassword() {
  // 8-32 位，含大写/小写/数字/特殊至少 3 类
  const pools = ["ABCDEFGHJKLMNPQRSTUVWXYZ", "abcdefghijkmnpqrstuvwxyz", "23456789", "!@#$%^&*"];
  const pick = (s) => s[Math.floor(Math.random() * s.length)];
  let chars = pools.map(pick);                       // 每类至少一个
  const all = pools.join("");
  for (let i = 0; i < 8; i++) chars.push(pick(all)); // 补到 12 位
  for (let i = chars.length - 1; i > 0; i--) {       // 洗牌
    const j = Math.floor(Math.random() * (i + 1));
    [chars[i], chars[j]] = [chars[j], chars[i]];
  }
  return chars.join("");
}

function resolveConfigPath(value) {
  const raw = value && value !== true ? String(value) : DEFAULT_CONFIG_PATH;
  const resolved = path.resolve(SKILL_ROOT, raw);
  if (resolved !== DEFAULT_CONFIG_PATH) {
    throw new Error(`只允许写入本 Skill 根目录下的 config.ini: ${DEFAULT_CONFIG_PATH}`);
  }
  return resolved;
}

function saveApiKey(apiKey, configPath) {
  if (!apiKey || !apiKey.startsWith("sk-")) {
    throw new Error("接口未返回有效 API Key");
  }
  const content = [
    "# 深知可信搜索 API 配置",
    "# 本文件由 scripts/register.mjs 在用户提供手机号和验证码后自动生成。",
    "# 不要上传、打包或公开分享本文件。",
    "",
    "[dkag]",
    `api_key=${apiKey}`,
    "",
  ].join("\n");
  fs.writeFileSync(configPath, content, { encoding: "utf8", mode: 0o600 });
}

async function main() {
  const a = parseArgs(process.argv.slice(2));
  const base = a.base || DEFAULT_BASE;
  const cmd = a._[0];

  if (cmd === "send") {
    if (!a.phone) { console.error("缺少 --phone"); process.exit(2); }
    const r = await post(base + "/sendMessage", { phone: a.phone, type: "register" });
    console.log(JSON.stringify(r));
    if (r.status) console.error("验证码已发送，请向用户索取收到的 6 位验证码后再执行 register。");
    process.exit(r.status ? 0 : 1);
  }

  if (cmd === "register") {
    if (!a.phone || !a.vcode) { console.error("缺少 --phone 或 --vcode"); process.exit(2); }
    const payload = {
      phone: a.phone,
      vcode: a.vcode,
      password: a.password && a.password !== true ? a.password : genPassword(),
      type: a.type && a.type !== true ? a.type : DEFAULT_TYPE,
      organ: a.organ && a.organ !== true ? a.organ : "个人",
      name: a.name && a.name !== true ? a.name : "用户",
      apiKeyName: a["apikey-name"] && a["apikey-name"] !== true ? a["apikey-name"] : "agent-key",
    };
    payload.channel = a.channel && a.channel !== true ? a.channel : DEFAULT_CHANNEL;
    const r = await post(base + "/register", payload);
    const data = r.data || {};
    const ok = Boolean(r.status) && Boolean(data.apiKey);
    let saved = false;
    let configPath = null;
    let saveError = null;
    if (ok) {
      try {
        configPath = resolveConfigPath(a.config);
        saveApiKey(data.apiKey, configPath);
        saved = true;
      } catch (e) {
        saveError = e && e.message ? e.message : String(e);
      }
    }
    console.log(JSON.stringify({
      status: ok && saved,
      msg: r.msg,
      url: data.url || null,
      configSaved: saved,
      configPath: saved ? path.relative(SKILL_ROOT, configPath) : null,
      saveError,
      fallbackRegisterUrl: FALLBACK_REGISTER_URL,
    }));
    process.exit(ok && saved ? 0 : 1);
  }

  console.error("用法: node register.mjs [--base URL] <send|register> ...");
  process.exit(2);
}

main();
