<template>
  <AgentDetailLayout :agents="agents" :selected-agent="selectedAgent" :loading="loading" @select="onSelect" @back="selectedAgent = null">
    <div v-if="!selectedAgent" class="text-center py-20 text-white/50 hidden md:block">
      <div class="text-3xl mb-2">🤖</div>
      <div>請選擇角色查看配置</div>
    </div>

    <div v-if="selectedAgent">
      <h2 class="text-lg font-semibold mb-4">{{ selectedAgent.display }} 配置</h2>

      <div class="space-y-2">
        <!-- 1. 基本配置 -->
        <div class="bg-ocean-800/50 rounded-lg border border-white/5 overflow-hidden">
          <div class="flex items-center px-4 py-3">
            <button @click="toggle('basic')" class="flex items-center gap-3 flex-1 hover:bg-white/5 rounded text-left -ml-2 pl-2 py-0.5">
              <span class="text-white/30">{{ open.basic ? '▼' : '▶' }}</span>
              <span class="font-medium">⚙️ 基本配置</span>
            </button>
            <button @click="resetBasicConfig()" type="button" class="ml-2 px-3 py-1 text-xs rounded bg-white/10 text-white/50 hover:text-white transition">🔄 恢復預設</button>
            <button :disabled="!dirty.basic" @click="saveSection('basic')" class="ml-1 px-3 py-1 text-xs rounded bg-cyan-600 text-white disabled:opacity-30 disabled:cursor-not-allowed hover:bg-cyan-500 transition">💾 儲存</button>
          </div>
          <div v-if="open.basic" @change.capture="markDirty('basic')" @input.capture="markDirty('basic')" class="px-4 pb-4 border-t border-white/5 space-y-4">
            <!-- Discord -->
            <fieldset class="border border-white/10 rounded-lg p-4">
              <legend class="text-sm text-cyan-400 px-1 font-medium">Discord</legend>
              <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                <Field label="角色訊息觸發" tip="allow_bot_messages — off=關閉、mentions=被提及時觸發、all=全部觸發">
                  <select v-model="cfg.discord.allow_bot_messages" class="field-input"><option value="off">關閉（off）</option><option value="mentions">被提及時觸發（mentions）</option><option value="all">全部觸發（all）</option></select>
                </Field>
                <Field label="使用者訊息觸發" tip="allow_user_messages — involved=參與對話時、mentions=被提及時、multibot-mentions=多角色提及時">
                  <select v-model="cfg.discord.allow_user_messages" class="field-input"><option value="multibot-mentions">多角色提及時（multibot-mentions）</option><option value="involved">參與對話時（involved）</option><option value="mentions">被提及時（mentions）</option></select>
                </Field>
                <Field label="最大對話輪數" tip="max_bot_turns — 建議範圍：1–1000，預設 100">
                  <input v-model.number="cfg.discord.max_bot_turns" type="number" min="1" max="1000" class="field-input">
                  <span v-if="rangeWarn(cfg.discord.max_bot_turns, 1, 1000)" class="text-xs text-red-400">超出建議範圍（1–1000）</span>
                </Field>
<!-- TODO: 等 OpenAB 升級後加回 message_processing_mode / max_buffered_messages / max_batch_tokens -->
              </div>
              <div class="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Field label="允許私訊" tip="allow_dm — 是否接受 DM 訊息">
                  <div class="flex items-center gap-2"><Toggle v-model="cfg.discord.allow_dm" /><span class="text-sm text-white/70">{{ cfg.discord.allow_dm ? '是' : '否' }}</span></div>
                </Field>
              </div>
              <div class="mt-4 space-y-3">
                <!-- 頻道 -->
                <Field label="允許所有頻道" tip="allow_all_channels — 開啟後不限頻道">
                  <div class="flex items-center gap-2"><Toggle v-model="cfg.discord.allow_all_channels" /><span class="text-sm text-white/70">{{ cfg.discord.allow_all_channels ? '是（不限頻道）' : '否（指定頻道）' }}</span></div>
                </Field>
                <Field v-show="!cfg.discord.allow_all_channels" label="允許頻道" tip="allowed_channels — 只有這些頻道的訊息會被處理">
                  <IdSelect v-model="cfg.discord.allowed_channels" :options="channelOptions" placeholder="頻道" />
                </Field>
                <!-- 使用者 -->
                <Field label="允許所有使用者" tip="allow_all_users — 開啟後不限使用者">
                  <div class="flex items-center gap-2"><Toggle v-model="cfg.discord.allow_all_users" /><span class="text-sm text-white/70">{{ cfg.discord.allow_all_users ? '是（不限使用者）' : '否（指定使用者）' }}</span></div>
                </Field>
                <Field v-show="!cfg.discord.allow_all_users" label="允許使用者" tip="allowed_users — 指定允許的使用者">
                  <IdSelect v-model="cfg.discord.allowed_users" :options="userOptions" placeholder="使用者" />
                </Field>
                <!-- 身分組 -->
                <Field label="允許身分組" tip="allowed_role_ids — 只有這些身分組的訊息會被處理。自己的同名身分組已鎖定">
                  <IdSelect v-model="cfg.discord.allowed_role_ids" :options="roleOptions" :locked-ids="lockedRoleIds" placeholder="身分組" />
                </Field>
                <!-- 信任角色 -->
                <Field label="信任的角色" tip="trusted_bot_ids — 這些角色的訊息會被當作可信來源處理">
                  <IdSelect v-model="cfg.discord.trusted_bot_ids" :options="botOptions" placeholder="角色" />
                </Field>
              </div>
            </fieldset>
            <!-- Agent -->
            <fieldset class="border border-white/10 rounded-lg p-4">
              <legend class="text-sm text-cyan-400 px-1 font-medium">代理程式（agent）</legend>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Field label="啟動指令" tip="command — Agent 的主要啟動程式"><input v-model="cfg.agent.command" class="field-input font-mono" placeholder="kiro-cli"></Field>
                <Field label="工作目錄" tip="working_dir — Agent 的工作路徑">
                  <div class="flex gap-2">
                    <input v-model="cfg.agent.working_dir" class="field-input font-mono flex-1">
                    <button @click="showWorkDir = true" type="button" class="px-2 py-1 text-xs rounded bg-ocean-700 border border-white/15 text-white/60 hover:text-white shrink-0">📂</button>
                  </div>
                </Field>
              </div>
              <div class="mt-3 space-y-3">
                <Field label="啟動參數" tip="args — 傳給 command 的參數列表"><TagInput v-model="cfg.agent.args" /></Field>
                <Field label="繼承環境變數" tip="inherit_env — 從容器傳入 Agent 的環境變數名稱"><TagInput v-model="cfg.agent.inherit_env" /></Field>
              </div>
            </fieldset>
            <!-- Pool -->
            <fieldset class="border border-white/10 rounded-lg p-4">
              <legend class="text-sm text-cyan-400 px-1 font-medium">連線池（pool）</legend>
              <div class="grid grid-cols-2 sm:grid-cols-3 gap-4">
                <Field label="工作階段數" tip="max_sessions — 建議範圍：1–100，預設 10"><input v-model.number="cfg.pool.max_sessions" type="number" min="1" max="100" class="field-input">
                  <span v-if="rangeWarn(cfg.pool.max_sessions, 1, 100)" class="text-xs text-red-400">超出建議範圍（1–100）</span></Field>
                <Field label="存活時數" tip="session_ttl_hours — 建議範圍：1–720，預設 24"><input v-model.number="cfg.pool.session_ttl_hours" type="number" min="1" max="720" class="field-input">
                  <span v-if="rangeWarn(cfg.pool.session_ttl_hours, 1, 720)" class="text-xs text-red-400">超出建議範圍（1–720）</span></Field>
              </div>
            </fieldset>
            <!-- Reactions -->
            <fieldset class="border border-white/10 rounded-lg p-4">
              <legend class="text-sm text-cyan-400 px-1 font-medium">表情回饋（reactions）</legend>
              <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Field label="啟用表情回饋" tip="reactions.enabled — 是否在訊息上添加 emoji 表示處理狀態">
                  <div class="flex items-center gap-2"><Toggle v-model="cfg.reactions.enabled" /><span class="text-sm text-white/70">{{ cfg.reactions.enabled ? '啟用' : '停用' }}</span></div>
                </Field>
                <Field label="回覆後移除" tip="remove_after_reply — 回覆完成後是否移除過程中的 emoji">
                  <div class="flex items-center gap-2"><Toggle v-model="cfg.reactions.remove_after_reply" /><span class="text-sm text-white/70">{{ cfg.reactions.remove_after_reply ? '是' : '否' }}</span></div>
                </Field>
                <Field label="工具顯示模式" tip="tool_display — full=完整 / compact=精簡 / none=不顯示">
                  <select v-model="cfg.reactions.tool_display" class="field-input"><option value="full">完整（full）</option><option value="compact">精簡（compact）</option><option value="none">不顯示（none）</option></select>
                </Field>
              </div>
              <div class="mt-4">
                <div class="flex items-center mb-2"><span class="text-sm text-white/60">表情符號設定</span><button @click="resetEmojis()" type="button" class="ml-auto text-xs px-2 py-0.5 rounded bg-white/10 text-white/50 hover:text-white">🔄 復原預設</button></div>
                <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
                  <Field v-for="(val, key) in cfg.reactions.emojis" :key="key" :label="emojiLabels[key] || key" :tip="'狀態：'+key">
                    <EmojiPicker v-if="key !== 'done'" v-model="cfg.reactions.emojis[key]" />
                    <div v-else class="flex items-center bg-ocean-800 border border-white/15 rounded px-3 py-2 text-xl opacity-60 cursor-not-allowed">🆗</div>
                  </Field>
                </div>
              </div>
              <!-- Reactions Mapping -->
              <div class="mt-4">
                <div class="text-sm text-white/60 mb-2">表情指令對照（reactions.mapping）</div>
                <div class="space-y-2">
                  <div v-for="item in mappingList" :key="item.emoji" class="flex items-center gap-2">
                    <div class="w-[60px] shrink-0"><EmojiPicker :model-value="item.emoji" @update:model-value="renameMapping(item.emoji, $event, item.cmd)" /></div>
                    <input :value="item.cmd" @change="updateMappingCmd(item.emoji, $event.target.value)" class="flex-1 field-input font-mono" placeholder="指令或 prompt">
                    <button @click="deleteMapping(item.emoji)" type="button" class="text-red-400/60 hover:text-red-400 text-lg shrink-0 w-8 text-center">✕</button>
                  </div>
                </div>
                <div class="flex items-center gap-2 mt-3">
                  <div class="w-[60px] shrink-0"><EmojiPicker v-model="newMapping.emoji" /></div>
                  <input v-model="newMapping.cmd" class="flex-1 field-input font-mono" placeholder="輸入指令或 prompt">
                  <button @click="addMapping()" type="button" class="px-3 py-1.5 text-xs rounded bg-cyan-600 text-white shrink-0">+ 新增</button>
                </div>
              </div>
            </fieldset>
            <!-- STT -->
            <fieldset class="border border-white/10 rounded-lg p-4 opacity-50 pointer-events-none relative">
              <legend class="text-sm text-white/40 px-1 font-medium">STT（語音轉文字）</legend>
              <div class="absolute inset-0 flex items-center justify-center z-10">
                <span class="bg-ocean-800 px-3 py-1.5 rounded text-sm text-white/60 border border-white/10">🚧 目前尚未開放</span>
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Field label="啟用"><Toggle :model-value="false" /></Field>
                <Field label="模型"><input value="whisper-large-v3" disabled class="field-input opacity-50"></Field>
                <Field label="API 位址"><input value="" disabled class="field-input opacity-50"></Field>
              </div>
            </fieldset>
            <!-- 排程設定 -->
            <fieldset class="border border-white/10 rounded-lg p-4">
              <legend class="text-sm text-cyan-400 px-1 font-medium">排程設定</legend>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Field label="使用者排程" tip="usercron_enabled — 是否啟用角色自訂的排程任務">
                  <div class="flex items-center gap-2"><Toggle v-model="cfg.cron.usercron_enabled" /><span class="text-sm text-white/70">{{ cfg.cron.usercron_enabled ? '啟用' : '停用' }}</span></div>
                </Field>
                <Field label="排程路徑" tip="usercron_path — 固定路徑，不可修改"><input value="cronjob.toml" disabled class="field-input font-mono opacity-50"></Field>
              </div>
            </fieldset>
          </div>
        </div>

        <!-- 2. MCP 配置 -->
        <div class="bg-ocean-800/50 rounded-lg border border-white/5 overflow-hidden">
          <div class="flex items-center px-4 py-3">
            <button @click="toggle('mcp')" class="flex items-center gap-3 flex-1 hover:bg-white/5 rounded text-left -ml-2 pl-2 py-0.5">
              <span class="text-white/30">{{ open.mcp ? '▼' : '▶' }}</span>
              <span class="font-medium">🔌 MCP 配置</span>
              <span class="ml-auto text-sm text-white/40">{{ mcpEnabledCount }}/{{ mockMcp.length }}</span>
            </button>
            <button :disabled="!dirty.mcp" @click="saveMcp()" class="ml-2 px-3 py-1 text-xs rounded bg-cyan-600 text-white disabled:opacity-30 disabled:cursor-not-allowed hover:bg-cyan-500 transition">💾 儲存</button>
          </div>
          <div v-if="open.mcp" @change.capture="markDirty('mcp')" @input.capture="markDirty('mcp')" class="px-4 pb-4 border-t border-white/5 space-y-2">
            <div class="flex justify-end mb-2">
              <router-link to="/mcp-servers" class="text-xs px-3 py-1.5 rounded bg-ocean-700 border border-white/15 text-white/60 hover:text-white no-underline">⚙️ MCP 伺服器管理</router-link>
            </div>
            <div v-for="s in mockMcp" :key="s.name" class="bg-ocean-700/50 rounded-lg overflow-hidden">
              <div class="flex items-center gap-2 px-3 py-2.5 cursor-pointer hover:bg-white/5" @click="s._open = !s._open">
                <input type="checkbox" :checked="s.enabled" :indeterminate.prop="s.partial" @click.stop="toggleMcpServer(s)" class="w-4 h-4 accent-cyan-500">
                <div class="flex-1 min-w-0">
                  <span class="text-sm" :class="s.enabled ? 'text-cyan-300' : 'text-white/40'">{{ s.name }}</span>
                  <span class="text-xs text-white/40 ml-2">{{ s.desc }}</span>
                </div>
                <span class="text-xs text-white/40">{{ s.enabledTools }}/{{ s.tools.length }} tools</span>
                <span class="text-xs text-white/30">{{ s._open ? '▼' : '▶' }}</span>
              </div>
              <div v-if="s._open" class="px-3 pb-3 border-t border-white/5">
                <div class="flex gap-2 py-2 mb-1">
                  <button @click="mcpSelectAll(s)" class="text-xs px-2 py-0.5 rounded bg-cyan-600/20 text-cyan-300 hover:bg-cyan-600/30">全選</button>
                  <button @click="mcpDeselectAll(s)" class="text-xs px-2 py-0.5 rounded bg-white/10 text-white/60 hover:bg-white/15">取消</button>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-1">
                  <label v-for="t in s.tools" :key="t.name" class="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-white/5 cursor-pointer text-sm">
                    <input type="checkbox" v-model="t.enabled" @change="updateMcpCount(s)" class="w-3.5 h-3.5 accent-cyan-500">
                    <span :class="t.enabled ? 'text-white/90' : 'text-white/40'">{{ t.name }}</span>
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 3. Skill 配置 -->
        <div class="bg-ocean-800/50 rounded-lg border border-white/5 overflow-hidden">
          <div class="flex items-center px-4 py-3">
            <button @click="toggle('skill')" class="flex items-center gap-3 flex-1 hover:bg-white/5 rounded text-left -ml-2 pl-2 py-0.5">
              <span class="text-white/30">{{ open.skill ? '▼' : '▶' }}</span>
              <span class="font-medium">📚 技能配置（Skill）</span>
              <span class="ml-auto text-sm text-white/40">{{ mockSkills.filter(s=>s.enabled).length }}/{{ mockSkills.length }}</span>
            </button>
            <button :disabled="!dirty.skill" @click="saveSkill()" class="ml-2 px-3 py-1 text-xs rounded bg-cyan-600 text-white disabled:opacity-30 disabled:cursor-not-allowed hover:bg-cyan-500 transition">💾 儲存</button>
          </div>
          <div v-if="open.skill" @change.capture="markDirty('skill')" @input.capture="markDirty('skill')" class="px-4 pb-4 border-t border-white/5">
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-1">
              <label v-for="s in mockSkills" :key="s.name" class="flex items-center gap-2 px-3 py-2.5 rounded hover:bg-white/5 cursor-pointer">
                <input type="checkbox" v-model="s.enabled" class="w-4 h-4 accent-cyan-500">
                <div class="min-w-0">
                  <span class="text-sm" :class="s.enabled ? 'text-white/90' : 'text-white/40'">{{ s.name }}</span>
                  <span class="text-xs text-white/40 ml-1">{{ s.desc }}</span>
                </div>
              </label>
            </div>
          </div>
        </div>

        <!-- 4. 排程任務 -->
        <div class="bg-ocean-800/50 rounded-lg border border-white/5 overflow-hidden">
          <div class="flex items-center px-4 py-3">
            <button @click="toggle('cron')" class="flex items-center gap-3 flex-1 hover:bg-white/5 rounded text-left -ml-2 pl-2 py-0.5">
              <span class="text-white/30">{{ open.cron ? '▼' : '▶' }}</span>
              <span class="font-medium">⏰ 排程任務</span>
              <span class="ml-auto text-sm text-white/40">{{ mockCrons.length }} 筆</span>
            </button>
            <button @click="loadCrons()" type="button" class="ml-2 text-xs px-2 py-0.5 rounded bg-white/10 text-white/50 hover:text-white">🔄</button>
            <button :disabled="!dirty.cron" @click="saveCron()" class="ml-1 px-3 py-1 text-xs rounded bg-cyan-600 text-white disabled:opacity-30 disabled:cursor-not-allowed hover:bg-cyan-500 transition">💾 儲存</button>
          </div>
          <div v-if="open.cron" @change.capture="markDirty('cron')" @input.capture="markDirty('cron')" class="px-4 pb-4 border-t border-white/5" :class="{'opacity-40 pointer-events-none': !cfg.cron.usercron_enabled}">
            <div class="space-y-2">
              <div v-for="(c, i) in visibleCrons" :key="i" class="bg-ocean-700/50 rounded px-4 py-3 flex items-center gap-3 cursor-pointer hover:bg-ocean-700/80" @click="editCron(c)">
                <span class="text-sm font-mono text-cyan-400 min-w-[100px]">{{ c.schedule }}</span>
                <span class="text-sm text-white/70 flex-1 truncate">{{ c.message }}</span>
                <span class="text-xs text-white/40 shrink-0">{{ getChannelName(c.channel_id) }}</span>
              </div>
            </div>
            <div v-if="mockCrons.length > cronLimit" class="mt-3 text-center">
              <button @click="cronLimit += 20" class="text-sm text-cyan-400 hover:underline">載入更多...</button>
            </div>
            <button @click="editCron(null)" class="mt-3 w-full py-2.5 rounded border border-dashed border-white/20 text-white/50 hover:text-white hover:border-white/40 text-sm">+ 新增排程任務</button>
          </div>
        </div>

        <!-- 5. 知識庫配置 -->
        <div class="bg-ocean-800/50 rounded-lg border border-white/5 overflow-hidden">
          <button @click="toggle('kb')" class="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/5 text-left">
            <span class="text-white/30">{{ open.kb ? '▼' : '▶' }}</span>
            <span class="font-medium">🧠 知識庫</span>
            <span class="ml-auto text-sm text-white/40">{{ mockKb.length }} 個</span>
          </button>
          <div v-if="open.kb" @change.capture="markDirty('kb')" @input.capture="markDirty('kb')" class="px-4 pb-4 border-t border-white/5">
            <div class="space-y-2">
              <div v-if="!mockKb.length" class="text-sm text-white/40 py-4">暫無知識庫</div>
              <div v-for="k in mockKb" :key="k.id" class="bg-ocean-700/50 rounded px-4 py-3 flex items-center gap-3">
                <span class="text-cyan-400">📖</span>
                <div class="flex-1 min-w-0">
                  <div class="text-sm text-white/90 truncate">{{ k.name }}</div>
                  <div class="text-xs text-white/40">{{ k.items }} 項 · {{ k.source }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 排程任務 Edit Dialog -->
      <div v-if="cronDialog" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="cronDialog = null">
        <div class="bg-ocean-700 rounded-xl w-full max-w-lg p-6 shadow-2xl border border-white/10">
          <h3 class="text-lg font-semibold mb-4">{{ cronDialog.isNew ? '新增' : '編輯' }}排程任務</h3>
          <div class="space-y-4">
            <Field label="排程時間" tip="5 欄位 POSIX cron：分 時 日 月 週">
              <select @change="applyCronTemplate($event.target.value); $event.target.value = ''" class="field-input mb-2">
                <option value="">預設模板...</option>
                <option value="0 * * * *">每小時</option>
                <option value="0 9 * * *">每天早上 9 點</option>
                <option value="0 9 * * 1">每週一早上 9 點</option>
                <option value="0 9 * * 1-5">平日早上 9 點</option>
              </select>
              <div class="grid grid-cols-5 gap-2">
                <div><label class="text-[10px] text-white/40 block mb-0.5">分(0-59)</label><input v-model="cronFields.min" class="field-input font-mono text-center" placeholder="*"></div>
                <div><label class="text-[10px] text-white/40 block mb-0.5">時(0-23)</label><input v-model="cronFields.hour" class="field-input font-mono text-center" placeholder="*"></div>
                <div><label class="text-[10px] text-white/40 block mb-0.5">日(1-31)</label><input v-model="cronFields.day" class="field-input font-mono text-center" placeholder="*"></div>
                <div><label class="text-[10px] text-white/40 block mb-0.5">月(1-12)</label><input v-model="cronFields.month" class="field-input font-mono text-center" placeholder="*"></div>
                <div><label class="text-[10px] text-white/40 block mb-0.5">週(0-7)</label><input v-model="cronFields.dow" class="field-input font-mono text-center" placeholder="*"></div>
              </div>
              <div class="mt-1 text-xs font-mono text-white/40">{{ cronExpression }}</div>
              <div v-if="cronError" class="mt-1 text-xs text-red-400">{{ cronError }}</div>
            </Field>
            <Field label="頻道" tip="要發送到的 Discord 頻道">
              <select v-model="cronDialog.channel_id" class="field-input">
                <option value="">請選擇頻道</option>
                <option v-for="ch in channelOptions" :key="ch.id" :value="ch.id">{{ ch.label }}</option>
              </select>
            </Field>
            <Field label="時區" tip="執行時區"><select v-model="cronDialog.timezone" class="field-input"><option>Asia/Taipei</option><option>UTC</option></select></Field>
            <Field label="啟用">
              <div class="flex items-center gap-2"><Toggle v-model="cronDialog.enabled" /><span class="text-sm text-white/70">{{ cronDialog.enabled ? '啟用' : '停用' }}</span></div>
            </Field>
            <Field label="訊息內容" tip="排程觸發時發送的完整 prompt"><textarea v-model="cronDialog.message" rows="6" class="field-input font-mono resize-y" placeholder="排程訊息內容"></textarea></Field>
          </div>
          <div class="flex gap-3 justify-end mt-5">
            <button @click="cronDialog = null" class="px-4 py-2 text-sm rounded-lg border border-white/20 text-white/70 hover:bg-white/10">取消</button>
            <button @click="saveCronDialog()" class="px-4 py-2 text-sm rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium">儲存</button>
          </div>
        </div>
      </div>

      <!-- Save Dialog -->
      <div v-if="saveDialogKey" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="saveDialogKey = null">
        <div class="bg-ocean-700 rounded-xl w-full max-w-xs p-6 shadow-2xl border border-white/10 text-center">
          <h3 class="text-lg font-semibold mb-4">儲存設定</h3>
          <p class="text-sm text-white/60 mb-5">選擇儲存方式</p>
          <div class="space-y-2">
            <button @click="doSave(false)" class="w-full py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-sm font-medium">💾 儲存</button>
            <button @click="doSave(true)" class="w-full py-2.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-sm font-medium">💾 儲存 + 重啟</button>
            <button @click="saveDialogKey = null" class="w-full py-2.5 rounded-lg border border-white/20 text-white/70 hover:bg-white/10 text-sm">取消</button>
          </div>
        </div>
      </div>

      <!-- Work Directory Dialog -->
      <div v-if="showWorkDir" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="showWorkDir = false">
        <div class="bg-ocean-700 rounded-xl w-full max-w-md p-6 shadow-2xl border border-white/10">
          <h3 class="text-lg font-semibold mb-2">📂 工作目錄</h3>
          <p class="text-sm text-white/50 mb-4 font-mono">{{ cfg.agent.working_dir }}</p>
          <div class="space-y-1 bg-ocean-800/50 rounded-lg p-3 max-h-60 overflow-y-auto">
            <div v-for="f in mockFiles" :key="f.name" class="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-white/5 text-sm">
              <span>{{ f.type === 'dir' ? '📁' : '📄' }}</span>
              <span :class="f.type === 'dir' ? 'text-cyan-300' : 'text-white/80'">{{ f.name }}</span>
              <span v-if="f.size" class="text-xs text-white/30 ml-auto">{{ f.size }}</span>
            </div>
          </div>
          <div class="flex justify-end mt-4">
            <button @click="showWorkDir = false" class="px-4 py-2 text-sm rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white">關閉</button>
          </div>
        </div>
      </div>
    </div>
  </AgentDetailLayout>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, nextTick } from 'vue'
import { useAgentList } from '../composables/useAgentList.js'
import { useApi } from '../composables/useApi.js'
import AgentDetailLayout from '../components/AgentDetailLayout.vue'
import Field from '../components/Field.vue'
import Toggle from '../components/Toggle.vue'
import TagInput from '../components/TagInput.vue'
import IdSelect from '../components/IdSelect.vue'
import EmojiPicker from '../components/EmojiPicker.vue'

const { get, post } = useApi()
const { agents, selectedAgent, loading, selectAgent, currentGroup } = useAgentList()

const open = reactive({ basic: true, mcp: false, skill: false, cron: false, kb: false })
const dirty = reactive({ basic: false, mcp: false, skill: false, cron: false, kb: false })
const cronLimit = ref(20)
const cronDialog = ref(null)
const showWorkDir = ref(false)

function toggle(key) { open[key] = !open[key] }
function onSelect(a) {
  ready.value = false
  selectAgent(a)
  Object.keys(dirty).forEach(k => dirty[k] = false)
  // Fallback: ensure ready becomes true even if loadConfig is slow
  setTimeout(() => { ready.value = true }, 500)
}

// Always load config when selectedAgent changes (covers auto-select on mount too)
watch(selectedAgent, (a) => {
  if (a) {
    ready.value = false
    Object.keys(dirty).forEach(k => dirty[k] = false)
    loadConfig(a.name)
    loadCrons()
    loadSkills()
    loadMcp()
    loadKb()
  }
})

const newMapping = ref({ emoji: '', cmd: '' })
function addMapping() {
  if (newMapping.value.emoji && newMapping.value.cmd) {
    if (!cfg.reactions.mapping) cfg.reactions.mapping = {}
    cfg.reactions.mapping[newMapping.value.emoji] = newMapping.value.cmd
    newMapping.value = { emoji: '', cmd: '' }
  }
}
const mappingList = computed(() => Object.entries(cfg.reactions.mapping || {}).map(([emoji, cmd]) => ({ emoji, cmd })))
function updateMappingCmd(emoji, cmd) { cfg.reactions.mapping[emoji] = cmd }
function deleteMapping(emoji) { delete cfg.reactions.mapping[emoji] }

const defaultEmojis = { queued: '👀', thinking: '🤔', tool: '🔥', coding: '👨‍💻', web: '⚡', done: '🆗', error: '😱' }

function resetEmojis() { Object.keys(cfg.reactions.emojis).forEach(k => delete cfg.reactions.emojis[k]); Object.assign(cfg.reactions.emojis, defaultEmojis) }

function resetBasicConfig() {
  cfg.discord.allow_bot_messages = 'off'
  cfg.discord.allow_user_messages = 'multibot-mentions'
  cfg.discord.max_bot_turns = 100
  cfg.discord.allow_all_channels = false
  cfg.discord.allow_all_users = false
  cfg.discord.allow_dm = false
  cfg.pool.max_sessions = 10
  cfg.pool.session_ttl_hours = 4
  cfg.reactions.enabled = true
  cfg.reactions.remove_after_reply = false
  cfg.reactions.tool_display = 'full'
  Object.assign(cfg.reactions.emojis, defaultEmojis)
}

async function loadMcp() {
  if (!selectedAgent.value) return
  const res = await get(`/api/mcp-servers/pool-for-agent/${selectedAgent.value.name}`)
  if (res?.servers) {
    const agentCfg = res.agent_config || {}
    const agentFilter = res.tool_filter || {}
    mockMcp.splice(0, mockMcp.length, ...res.servers.map(s => {
      const cfg = agentCfg[s.id]
      const isEnabled = cfg?.enabled ?? false
      const filterTools = agentFilter[s.id] || []
      const tools = s.tools.map(t => ({
        name: t,
        enabled: isEnabled && (filterTools.length === 0 || filterTools.includes(t))
      }))
      const enabledTools = tools.filter(t => t.enabled).length
      return {
        id: s.id, name: s.name, desc: s.description || '', env: cfg?.env || 'local',
        enabled: isEnabled, partial: enabledTools > 0 && enabledTools < tools.length,
        _open: false, enabledTools, tools
      }
    }))
  }
}

async function saveMcp() {
  if (!selectedAgent.value) return
  const config = {}
  const toolFilter = {}
  mockMcp.forEach(s => {
    if (s.enabled && s.id) {
      config[String(s.id)] = { env: s.env || 'local', enabled: true }
      const enabledTools = s.tools.filter(t => t.enabled).map(t => t.name)
      if (enabledTools.length < s.tools.length) {
        toolFilter[String(s.id)] = enabledTools
      }
    }
  })
  console.log('[saveMcp] payload:', { config, toolFilter })
  const res = await post(`/api/mcp-servers/save-agent-config/${selectedAgent.value.name}`, { config, toolFilter })
  if (res?.ok) dirty.mcp = false
  console.log('[saveMcp] result:', res)
}

async function saveSkill() {
  if (!selectedAgent.value) return
  const enabled = mockSkills.filter(s => s.enabled).map(s => s.name)
  const res = await fetch(`/api/agents/${selectedAgent.value.name}/skills`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ enabled_skills: enabled })
  })
  if (res.ok) dirty.skill = false
  console.log('[saveSkill]', enabled, await res.json())
}

async function loadSkills() {
  if (!selectedAgent.value) return
  const [availRes, agentSkills] = await Promise.all([
    get('/api/skills/available'),
    Promise.resolve(selectedAgent.value.skills || [])
  ])
  if (availRes?.skills) {
    mockSkills.splice(0, mockSkills.length, ...availRes.skills.map(s => ({
      name: s.name,
      desc: s.description ? `${s.description}（${s.name}）` : s.name,
      enabled: agentSkills.includes(s.name)
    })))
  }
}

async function saveCron() {
  if (!selectedAgent.value) return
  // Build TOML content from mockCrons
  const lines = mockCrons.map(c => {
    let block = '[[jobs]]\n'
    block += `schedule = "${c.schedule}"\n`
    block += `channel = "${c.channel_id}"\n`
    block += `message = "${c.message}"\n`
    if (c.timezone) block += `timezone = "${c.timezone}"\n`
    if ('enabled' in c) block += `enabled = ${c.enabled}\n`
    return block
  }).join('\n')
  const res = await fetch(`/api/agents/${selectedAgent.value.name}/cronjob`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content: lines })
  })
  if (res.ok) dirty.cron = false
  console.log('[saveCron]', await res.json())
}

async function loadCrons() {
  if (!selectedAgent.value) return
  const res = await get(`/api/agents/${selectedAgent.value.name}/cronjob`)
  console.log('[loadCrons]', res)
  if (res?.jobs) {
    mockCrons.splice(0, mockCrons.length, ...res.jobs)
  } else {
    mockCrons.splice(0, mockCrons.length)
  }
}
function renameMapping(oldEmoji, newEmoji, cmd) {
  delete cfg.reactions.mapping[oldEmoji]
  cfg.reactions.mapping[newEmoji] = cmd
}

async function loadConfig(agentName) {
  const res = await get(`/api/agents/${agentName}/config`)
  console.log('[loadConfig]', agentName, 'parsed:', res?.parsed)
  if (res?.parsed && Object.keys(res.parsed).length) {
    const p = res.parsed
    if (p.discord) {
      const d = p.discord
      if ('allow_bot_messages' in d) cfg.discord.allow_bot_messages = d.allow_bot_messages
      if ('allow_user_messages' in d) cfg.discord.allow_user_messages = d.allow_user_messages
      if ('max_bot_turns' in d) cfg.discord.max_bot_turns = d.max_bot_turns
      cfg.discord.allowed_channels = Array.isArray(d.allowed_channels) ? d.allowed_channels : []
      cfg.discord.allowed_role_ids = Array.isArray(d.allowed_role_ids) ? d.allowed_role_ids : []
      cfg.discord.trusted_bot_ids = (Array.isArray(d.trusted_bot_ids) ? d.trusted_bot_ids : []).filter(id => !selectedAgent.value || String(id) !== String(selectedAgent.value.bot_id))
      cfg.discord.allowed_users = Array.isArray(d.allowed_users) ? d.allowed_users : []
      if ('allow_all_channels' in d) cfg.discord.allow_all_channels = d.allow_all_channels
      if ('allow_all_users' in d) cfg.discord.allow_all_users = d.allow_all_users
      if ('allow_dm' in d) cfg.discord.allow_dm = d.allow_dm
    }
    if (p.agent) {
      if ('command' in p.agent) cfg.agent.command = p.agent.command
      if ('working_dir' in p.agent) cfg.agent.working_dir = p.agent.working_dir
      cfg.agent.args = Array.isArray(p.agent.args) ? p.agent.args : []
      cfg.agent.inherit_env = Array.isArray(p.agent.inherit_env) ? p.agent.inherit_env : []
    }
    if (p.pool) {
      if ('max_sessions' in p.pool) cfg.pool.max_sessions = p.pool.max_sessions
      if ('session_ttl_hours' in p.pool) cfg.pool.session_ttl_hours = p.pool.session_ttl_hours
    }
    if (p.reactions) {

      if ('enabled' in p.reactions) cfg.reactions.enabled = p.reactions.enabled
      if ('remove_after_reply' in p.reactions) cfg.reactions.remove_after_reply = p.reactions.remove_after_reply
      if ('tool_display' in p.reactions) cfg.reactions.tool_display = p.reactions.tool_display
      if (p.reactions.emojis && typeof p.reactions.emojis === 'object') Object.assign(cfg.reactions.emojis, p.reactions.emojis)
      if (p.reactions.mapping && typeof p.reactions.mapping === 'object') cfg.reactions.mapping = { ...p.reactions.mapping }
    }
    if (p.cron) {
      if ('usercron_enabled' in p.cron) cfg.cron.usercron_enabled = p.cron.usercron_enabled
      if ('usercron_path' in p.cron) cfg.cron.usercron_path = p.cron.usercron_path
    }
  }
  nextTick(() => { ready.value = true })
}
function getChannelName(id) { const ch = channelOptions.value.find(c => c.id === id); return ch ? ch.label : id }
function markDirty(key) { dirty[key] = true }
function rangeWarn(val, min, max) { return val !== '' && val !== null && (val < min || val > max) }
function saveSection(key) { saveDialogKey.value = key }
const saveDialogKey = ref(null)
async function doSave(restart) {
  const key = saveDialogKey.value
  saveDialogKey.value = null
  // Send cfg to PATCH API
  if (selectedAgent.value) {
    const payload = JSON.parse(JSON.stringify(cfg))
    console.log('[doSave]', selectedAgent.value.name, 'payload:', payload)
    const res = await fetch(`/api/agents/${selectedAgent.value.name}/config`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    if (res.ok) dirty[key] = false
    if (restart) {
      await post(`/api/restart/${selectedAgent.value.name}`)
    }
  }
}

async function loadKb() {
  if (!selectedAgent.value) return
  const res = await get(`/api/agents/${selectedAgent.value.name}/kb`)
  if (res?.contexts) {
    mockKb.splice(0, mockKb.length, ...res.contexts.map(c => ({
      id: c.id || c.name, name: c.name, items: c.item_count || 0, source: c.source_path || ''
    })))
  } else {
    mockKb.splice(0, mockKb.length)
  }
}

// Deep watchers for dirty tracking — defined after data declarations below
const ready = ref(false)
onMounted(() => nextTick(() => { ready.value = true }))

// ID → Name mapping (mock)
const channelMap = { '1492090122257170526': '🍔 蟹堡王', '1503940169252999198': '🏖️ 廣場', '1503704375074361424': '🧪 實驗室' }
const botMap = { '1493800835853975562': '小蝸', '1496023645083009024': '派大星', '1503574146117013555': '泡芙老師' }
const emojiLabels = { thinking: '思考中', tool_use: '使用工具', responding: '回覆中', done: '完成', error: '錯誤', queued: '排隊中', cancelled: '已取消' }

// Dropdown options
// Dropdown options (channels loaded from API)
const channelOptions = ref([])
async function loadChannels() {
  const group = currentGroup.value
  console.log('[AgentConfig] loadChannels group=', group)
  const res = await get(`/api/discord/channels?group=${group}`)
  if (res?.channels) {
    channelOptions.value = res.channels.map(ch => ({ id: String(ch.id), label: `# ${ch.name}` }))
  } else {
    channelOptions.value = []
  }
}
loadChannels()
watch(currentGroup, () => nextTick(loadChannels))

const roleOptions = ref([])
async function loadRoles() {
  const group = currentGroup.value
  console.log('[AgentConfig] loadRoles group=', group)
  const res = await get(`/api/discord/roles?group=${group}`)
  if (res?.roles) {
    roleOptions.value = res.roles.map(r => {
      const hex = r.color ? '#' + r.color.toString(16).padStart(6, '0') : ''
      return { id: String(r.id), label: r.name, color: hex }
    })
  } else {
    roleOptions.value = []
  }
}
loadRoles()
watch(currentGroup, () => nextTick(loadRoles))

// Bot's own role is locked (can't be removed from allowed_role_ids)
const lockedRoleIds = computed(() => {
  if (!selectedAgent.value) return []
  const display = selectedAgent.value.display || ''
  const name = selectedAgent.value.name || ''
  console.log('[lockedRoleIds] agent display:', display, 'name:', name, 'roles:', roleOptions.value.map(r => r.label))
  // Match: role name equals display, or role name is contained in display, or display contains role name
  const ownRole = roleOptions.value.find(r =>
    r.label === display || r.label === name || display.includes(r.label) || r.label.includes(display)
  )
  return ownRole ? [ownRole.id] : []
})

// Ensure bot's own role is always in allowed_role_ids
watch([selectedAgent, roleOptions], () => {
  if (lockedRoleIds.value.length && !cfg.discord.allowed_role_ids.some(id => String(id) === String(lockedRoleIds.value[0]))) {
    cfg.discord.allowed_role_ids.push(lockedRoleIds.value[0])
  }
})
const botOptions = ref([])
async function loadBots() {
  const group = currentGroup.value
  console.log('[AgentConfig] loadBots group=', group)
  const res = await get(`/api/discord/members?group=${group}`)
  if (res?.members) {
    botOptions.value = res.members
      .filter(m => m.bot && (!selectedAgent.value || String(m.id) !== String(selectedAgent.value.bot_id)))
      .map(m => ({ id: String(m.id), label: m.name, avatar: m.avatar ? `https://cdn.discordapp.com/avatars/${m.id}/${m.avatar}.png?size=32` : '' }))
    userOptions.value = res.members
      .filter(m => !m.bot)
      .map(m => ({ id: String(m.id), label: m.name, avatar: m.avatar ? `https://cdn.discordapp.com/avatars/${m.id}/${m.avatar}.png?size=32` : '' }))
  } else {
    botOptions.value = []
    userOptions.value = []
  }
}
const userOptions = ref([])
loadBots()
watch(currentGroup, () => nextTick(loadBots))
watch(selectedAgent, () => nextTick(loadBots))

// Mock work directory files
const mockFiles = [
  { name: '_projects.md', type: 'file', size: '1.5 KB' },
  { name: 'ai-chatbox/', type: 'dir' },
  { name: 'als/', type: 'dir' },
  { name: 'bikini-bottom/', type: 'dir' },
  { name: 'company-knowledge-base/', type: 'dir' },
  { name: 'mes-frontend/', type: 'dir' },
  { name: 'video-digest-push/', type: 'dir' },
]

// ─── Mock Data ───
const cfg = reactive({
  discord: { allow_bot_messages: 'mentions', allow_user_messages: 'multibot-mentions', max_bot_turns: 100, allowed_channels: [], allowed_role_ids: [], trusted_bot_ids: [], allowed_users: [], allow_all_channels: false, allow_all_users: false, allow_dm: false },
  agent: { command: 'kiro', args: ['chat', '--json'], working_dir: '/home/agent/projects', inherit_env: ['GH_TOKEN', 'AWS_REGION'] },
  pool: { max_sessions: 3, session_ttl_hours: 4 },
  reactions: { enabled: true, remove_after_reply: true, tool_display: 'full', emojis: { thinking: '🤔', tool_use: '🔧', responding: '✍️', done: '✅', error: '❌', queued: '📋', cancelled: '🚫' }, mapping: {} },
  cron: { usercron_enabled: true, usercron_path: '~/.openab/cronjob.toml' },
})

const mockMcp = reactive([])

const mcpEnabledCount = computed(() => mockMcp.filter(s => s.enabled).length)
function toggleMcpServer(s) { s.enabled = !s.enabled; s.tools.forEach(t => { t.enabled = s.enabled }); updateMcpCount(s) }
function mcpSelectAll(s) { s.tools.forEach(t => { t.enabled = true }); updateMcpCount(s) }
function mcpDeselectAll(s) { s.tools.forEach(t => { t.enabled = false }); updateMcpCount(s) }
function updateMcpCount(s) { s.enabledTools = s.tools.filter(t => t.enabled).length; s.enabled = s.enabledTools > 0; s.partial = s.enabledTools > 0 && s.enabledTools < s.tools.length }

const mockSkills = reactive([])

const mockCrons = reactive([])
const visibleCrons = computed(() => mockCrons.slice(0, cronLimit.value))
function editCron(c) {
  const parts = c ? c.schedule.split(' ') : ['', '', '', '', '']
  cronFields.min = parts[0] || '*'
  cronFields.hour = parts[1] || '*'
  cronFields.day = parts[2] || '*'
  cronFields.month = parts[3] || '*'
  cronFields.dow = parts[4] || '*'
  cronDialog.value = c ? { ...c, isNew: false } : { schedule: '', message: '', channel_id: '', timezone: 'Asia/Taipei', enabled: true, isNew: true }
}

const cronFields = reactive({ min: '*', hour: '*', day: '*', month: '*', dow: '*' })
const cronExpression = computed(() => `${cronFields.min} ${cronFields.hour} ${cronFields.day} ${cronFields.month} ${cronFields.dow}`)
const cronError = computed(() => {
  const valid = /^[\d,\-\*\/]+$/
  for (const v of [cronFields.min, cronFields.hour, cronFields.day, cronFields.month, cronFields.dow]) {
    if (v && !valid.test(v)) return `格式不合法：${v}`
  }
  return ''
})

function applyCronTemplate(expr) {
  if (!expr) return
  const parts = expr.split(' ')
  cronFields.min = parts[0] || '*'
  cronFields.hour = parts[1] || '*'
  cronFields.day = parts[2] || '*'
  cronFields.month = parts[3] || '*'
  cronFields.dow = parts[4] || '*'
}

function saveCronDialog() {
  const d = cronDialog.value
  const schedule = cronExpression.value
  console.log('[saveCronDialog]', d, 'schedule:', schedule)
  if (!schedule.trim() || !d.message) { console.log('[saveCronDialog] missing schedule or message'); return }
  if (cronError.value) return
  if (d.isNew) {
    mockCrons.push({ schedule, message: d.message, channel_id: d.channel_id, timezone: d.timezone, enabled: d.enabled })
  } else {
    const idx = mockCrons.findIndex(c => c.schedule === d.schedule && c.message === d.message)
    if (idx >= 0) Object.assign(mockCrons[idx], { ...d, schedule })
  }
  console.log('[saveCronDialog] mockCrons.length:', mockCrons.length)
  cronDialog.value = null
  dirty.cron = true
}

const mockKb = reactive([])


// Deep watchers for dirty tracking
watch(cfg, () => { if (ready.value) dirty.basic = true }, { deep: true })
watch(mockMcp, () => { if (ready.value) dirty.mcp = true }, { deep: true })
watch(mockSkills, () => { if (ready.value) dirty.skill = true }, { deep: true })
watch(mockCrons, () => { if (ready.value) dirty.cron = true }, { deep: true })
</script>

<style scoped>
.field-input {
  @apply w-full bg-ocean-800 border border-white/15 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-400/50;
}
</style>
