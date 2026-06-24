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
//   default: 該 agent 所有 server 預設連到哪個環境
//   overrides: 個別 server 要連到不同環境時指定
//
// 環境代碼：
//   prod  = http://mcp.twkd.com:1601    （正式）
//   beta  = http://192.168.1.105:1601   （測試）
//   local = http://host.docker.internal:80（本地 docker）
//
const AGENT_MCP_CONFIGS = (() => {
  // Prefer agent-configs.json (managed by admin UI) if it exists
  const jsonPath = path.join(CONFIGS_DIR, 'agent-configs.json');
  if (fs.existsSync(jsonPath)) {
    try {
      const data = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
      if (Object.keys(data).length > 0) return data;
    } catch (e) {
      console.warn('⚠️  agent-configs.json parse error, falling back to inline config');
    }
  }

  // Fallback: inline config (legacy)
  return {
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
})();

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

  const disabled = agentConfig.disabled || [];
  const toolFilter = agentConfig.toolFilter || {};
  const mcpServers = {};

  for (const serverName of profile.servers) {
    // Skip disabled servers
    if (disabled.includes(serverName)) continue;

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

    const entry = {
      url,
      headers: {
        Authorization: `Bearer ${env.token}`
      }
    };

    // autoApprove: use toolFilter if specified, otherwise use all from server def
    const approvedTools = toolFilter[serverName] || serverDef.autoApprove || [];
    if (approvedTools.length > 0) {
      entry.autoApprove = approvedTools;
    }

    mcpServers[serverName] = entry;
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

  console.log(`   Profile: ${config.profile} | Default env: ${config.default}${config.disabled?.length ? ' | Disabled: ' + config.disabled.join(', ') : ''}`);

  const result = generateMcpJson(agentName);
  if (!result) continue;

  // 顯示每個 server 的環境歸屬
  const disabled = config.disabled || [];
  const envSummary = {};
  for (const serverName of profiles[config.profile].servers) {
    if (disabled.includes(serverName)) continue;
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
