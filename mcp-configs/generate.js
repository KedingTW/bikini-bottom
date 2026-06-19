#!/usr/bin/env node
/**
 * MCP Config Generator
 * 
 * 根據 agent 的設定生成 .kiro/settings/mcp.json
 * 支援每個 server 獨立指定環境（prod / beta / local）
 * 
 * 用法：
 *   node mcp-configs/generate.js [agent-name]    # 生成指定 agent
 *   node mcp-configs/generate.js --all           # 生成所有 agent
 *   node mcp-configs/generate.js --dry-run bob   # 預覽不寫入
 *   node mcp-configs/generate.js --show bob      # 顯示完整 JSON 內容
 */

const fs = require('fs');
const path = require('path');

// ─── 載入定義 ───
const CONFIGS_DIR = path.resolve(__dirname);
const AGENTS_DIR = path.resolve(__dirname, '..', 'agents');

const servers = JSON.parse(fs.readFileSync(path.join(CONFIGS_DIR, 'servers.json'), 'utf8'));
const environments = {};
const profiles = {};

// 載入所有環境
for (const file of fs.readdirSync(path.join(CONFIGS_DIR, 'environments'))) {
  if (file.endsWith('.json')) {
    const name = file.replace('.json', '');
    environments[name] = JSON.parse(fs.readFileSync(path.join(CONFIGS_DIR, 'environments', file), 'utf8'));
  }
}

// 載入所有 profiles
for (const file of fs.readdirSync(path.join(CONFIGS_DIR, 'profiles'))) {
  if (file.endsWith('.json')) {
    const name = file.replace('.json', '');
    profiles[name] = JSON.parse(fs.readFileSync(path.join(CONFIGS_DIR, 'profiles', file), 'utf8'));
  }
}

// ─── Agent MCP 設定 ───
// 
// 設計邏輯：
//   profile: 該 agent 使用哪個 server 組合包（full / minimal）
//   default: 該 agent 所有 server 預設連到哪個環境
//   overrides: 個別 server 要連到不同環境時指定
//   disabled: 從 profile 中排除的 server（選填）
//   toolFilter: per-server tool 篩選（選填）
//     - 未指定的 server = 使用全部 autoApprove tools
//     - 指定空陣列 = 該 server 不自動核准任何 tool
//
// 環境代碼：
//   prod  = http://mcp.twkd.com:1601    （正式）
//   beta  = http://192.168.1.105:1601   （測試）
//   local = http://host.docker.internal:80（本地 docker）
//
const AGENT_MCP_CONFIGS = {
  bob: {
    profile: 'full',
    default: 'local',
    overrides: {
      // bob 大部分走本地，但以下走正式（因為本地沒有這些服務）
      'file-mcp':       'prod',
      'stt-mcp':        'prod',
      'image-mcp':      'prod',
      'wecom-push-mcp': 'prod',
    }
  },
  patrick: {
    profile: 'full',
    default: 'local',
    overrides: {}
  },
  squidward: {
    profile: 'full',
    default: 'local',
    overrides: {
      'hrs-mcp': 'beta',
      'sap-mcp': 'beta',
    }
  },
  puff: {
    profile: 'full',
    default: 'local',
    overrides: {}
  },
  larry: {
    profile: 'full',
    default: 'local',
    overrides: {}
  },
  gary: {
    profile: 'minimal',
    default: 'local',
    overrides: {}
  },
  sandy: {
    profile: 'minimal',
    default: 'local',
    overrides: {}
  }
};

// ─── 生成邏輯 ───

function generateMcpJson(agentName) {
  const agentConfig = AGENT_MCP_CONFIGS[agentName];
  if (!agentConfig) {
    console.error(`No MCP config defined for agent: ${agentName}`);
    return null;
  }

  const profile = profiles[agentConfig.profile];
  if (!profile) {
    throw new Error(`Unknown profile: ${agentConfig.profile}`);
  }

  // Determine which servers are enabled (profile servers minus disabled)
  const disabledServers = agentConfig.disabled || [];
  const enabledServers = profile.servers.filter(s => !disabledServers.includes(s));

  const mcpServers = {};

  for (const serverName of enabledServers) {
    const serverDef = servers.servers[serverName];
    if (!serverDef) {
      console.warn(`  ⚠️  Server "${serverName}" in profile but not in servers.json, skipping`);
      continue;
    }

    // 決定這個 server 用哪個環境
    const envName = agentConfig.overrides[serverName] || agentConfig.default;
    const env = environments[envName];
    if (!env) {
      throw new Error(`Unknown environment "${envName}" for server "${serverName}" in agent "${agentName}"`);
    }

    const url = env.baseUrl + serverDef.path;

    // Determine autoApprove: per-agent toolFilter or full server autoApprove
    let autoApprove = serverDef.autoApprove || [];
    if (agentConfig.toolFilter && agentConfig.toolFilter[serverName]) {
      // Only include tools that exist in the server's autoApprove list
      const allowed = agentConfig.toolFilter[serverName];
      autoApprove = autoApprove.filter(t => allowed.includes(t));
    }

    mcpServers[serverName] = {
      url,
      headers: {
        Authorization: `Bearer ${env.token}`
      },
      ...(autoApprove.length > 0 && { autoApprove })
    };
  }

  return { mcpServers };
}

// ─── CLI ───

const args = process.argv.slice(2);
const dryRun = args.includes('--dry-run');
const showJson = args.includes('--show');
const filteredArgs = args.filter(a => !a.startsWith('--'));

let agentNames;
if (args.includes('--all')) {
  agentNames = Object.keys(AGENT_MCP_CONFIGS);
} else if (filteredArgs.length > 0) {
  agentNames = filteredArgs;
} else {
  console.log('MCP Config Generator');
  console.log('====================\n');
  console.log('用法：');
  console.log('  node mcp-configs/generate.js bob              # 生成 bob');
  console.log('  node mcp-configs/generate.js --all            # 生成所有');
  console.log('  node mcp-configs/generate.js --dry-run bob    # 預覽');
  console.log('  node mcp-configs/generate.js --show bob       # 顯示完整 JSON');
  console.log('');
  console.log('已定義的 agents：', Object.keys(AGENT_MCP_CONFIGS).join(', '));
  console.log('可用 profiles：', Object.keys(profiles).join(', '));
  console.log('可用 environments：', Object.keys(environments).join(', '));
  console.log('');
  console.log('環境對照：');
  for (const [name, env] of Object.entries(environments)) {
    console.log(`  ${name.padEnd(6)} → ${env.baseUrl}`);
  }
  process.exit(0);
}

for (const agentName of agentNames) {
  console.log(`\n🔧 ${agentName}`);

  const config = AGENT_MCP_CONFIGS[agentName];
  if (!config) {
    console.error(`   ❌ No config defined for "${agentName}"`);
    continue;
  }

  console.log(`   Profile: ${config.profile} | Default env: ${config.default}`);

  const result = generateMcpJson(agentName);
  if (!result) continue;

  // 顯示每個 server 的環境歸屬
  const envSummary = {};
  for (const serverName of profiles[config.profile].servers) {
    const envName = config.overrides[serverName] || config.default;
    if (!envSummary[envName]) envSummary[envName] = [];
    envSummary[envName].push(serverName);
  }
  for (const [envName, svrs] of Object.entries(envSummary)) {
    const env = environments[envName];
    console.log(`   [${envName}] ${env.baseUrl}`);
    console.log(`      └─ ${svrs.join(', ')}`);
  }

  const outputPath = path.join(AGENTS_DIR, agentName, '.kiro', 'settings', 'mcp.json');
  const content = JSON.stringify(result, null, 2) + '\n';

  if (showJson) {
    console.log(`\n${content}`);
  }

  if (dryRun || showJson) {
    console.log(`   [DRY RUN] Would write to: ${outputPath}`);
  } else {
    const dir = path.dirname(outputPath);
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(outputPath, content, 'utf8');
    console.log(`   ✅ Written: ${outputPath}`);
  }
}

console.log('\nDone!');
