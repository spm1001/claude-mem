# Moltbot Architecture Summary

*Generated from source exploration. For the agent to understand its own internals.*

---

## 1. High-Level Architecture

Moltbot is a **gateway-based multi-channel AI agent framework**. The architecture separates concerns cleanly:

```
┌─────────────────────────────────────────────────────────────────┐
│                         GATEWAY                                  │
│  (HTTP/WebSocket server - src/gateway/)                         │
│  - Central orchestrator                                         │
│  - Manages sessions, channels, agents, config                   │
│  - Exposes API for CLI, mobile apps, web UIs                    │
└───────────────┬────────────────────────────────────┬────────────┘
                │                                    │
        ┌───────▼───────┐                   ┌────────▼────────┐
        │   CHANNELS    │                   │     AGENTS      │
        │ (extensions/) │                   │  (src/agents/)  │
        │ telegram      │                   │ pi-embedded     │
        │ discord       │                   │ system-prompt   │
        │ whatsapp      │                   │ tools           │
        │ signal, etc.  │                   │ sessions        │
        └───────────────┘                   └─────────────────┘
```

### Core Flow
1. **Message arrives** via a channel (Telegram, WhatsApp, etc.)
2. **Gateway routes** to the correct agent + session
3. **Agent runs** with tools, skills, context
4. **Response flows back** through the channel

### Session Keys
Sessions are identified by hierarchical keys:
- `agent:main:main` - Main agent, main session
- `agent:main:telegram:dm:12345` - Per-peer DM session
- `agent:main:discord:group:server123` - Group session
- `agent:main:subagent:<uuid>` - Spawned subagent session

The session key system (`src/routing/session-key.ts`) controls:
- Conversation isolation (per-peer, per-group, or shared main)
- Agent routing (multi-agent support)
- Thread handling

---

## 2. The Tool System

Tools are what give the agent its capabilities. There are several layers:

### Core Coding Tools (from @mariozechner/pi-coding-agent)
These are the foundation - inherited from the pi-coding-agent library:
- `read` / `write` / `edit` - File operations
- `exec` / `process` - Shell command execution
- `grep` / `find` / `ls` - Filesystem exploration

### Moltbot-Specific Tools (`src/agents/pi-tools.ts`)
Moltbot wraps and extends the core tools:

```typescript
export function createMoltbotCodingTools(options) {
  // 1. Create base coding tools
  // 2. Add Moltbot-specific tools:
  //    - browser, canvas, nodes, cron, message, gateway
  //    - tts, image, web_search, web_fetch
  // 3. Apply tool policies (allowlists, denylists)
  // 4. Wrap with sandbox context if applicable
  return tools;
}
```

### Tool Policy System (`src/agents/pi-tools.policy.ts`)
Tools can be filtered by:
- **Global policy** - `tools.policy.allow/deny` in config
- **Provider policy** - Different tools for different LLM providers
- **Agent policy** - Per-agent tool restrictions
- **Group policy** - Channel/group-specific restrictions
- **Subagent policy** - Inherited from parent session

### Sandbox Integration
When sandboxing is enabled, tools are wrapped to execute in Docker:
- `createSandboxedReadTool`, `createSandboxedWriteTool`, `createSandboxedEditTool`
- Exec commands run inside the sandbox container
- File paths are mapped between host and sandbox

### Channel-Specific Tools
Channels can provide their own tools via `agentTools` in the plugin:
```typescript
agentTools?: ChannelAgentToolFactory | ChannelAgentTool[];
```

---

## 3. How Channels Work

Channels are implemented as **plugins** in `extensions/`. Each channel implements the `ChannelPlugin` interface:

### Plugin Structure (`src/channels/plugins/types.plugin.ts`)
```typescript
type ChannelPlugin<ResolvedAccount> = {
  id: ChannelId;
  meta: ChannelMeta;
  capabilities: ChannelCapabilities;
  
  // Core adapters
  config: ChannelConfigAdapter;      // Account management
  security?: ChannelSecurityAdapter; // DM policy, allowlists
  outbound?: ChannelOutboundAdapter; // Sending messages
  gateway?: ChannelGatewayAdapter;   // Real-time handlers
  
  // Optional adapters
  pairing?: ChannelPairingAdapter;   // User approval flow
  threading?: ChannelThreadingAdapter;
  messaging?: ChannelMessagingAdapter;
  actions?: ChannelMessageActionAdapter;
  agentTools?: ChannelAgentToolFactory;
  // ... many more
};
```

### Example: Telegram Channel (`extensions/telegram/src/channel.ts`)
```typescript
export const telegramPlugin: ChannelPlugin<ResolvedTelegramAccount> = {
  id: "telegram",
  meta: { ...getChatChannelMeta("telegram") },
  capabilities: {
    chatTypes: ["direct", "group", "channel", "thread"],
    reactions: true, threads: true, media: true,
    nativeCommands: true, blockStreaming: true,
  },
  config: {
    listAccountIds: (cfg) => listTelegramAccountIds(cfg),
    resolveAccount: (cfg, accountId) => resolveTelegramAccount({ cfg, accountId }),
    // ...
  },
  security: {
    resolveDmPolicy: ({ cfg, accountId, account }) => { /* ... */ }
  },
  outbound: {
    send: async (ctx) => { /* ... */ }
  }
};
```

### Plugin Registry (`src/plugins/runtime.ts`)
Channels are registered at startup:
```typescript
type PluginRegistry = {
  channels: ChannelPlugin[];
  tools: PluginTool[];
  hooks: PluginHook[];
  providers: PluginProvider[];
  // ...
};
```

### Multi-Account Support
Each channel supports multiple accounts (e.g., multiple Telegram bots):
- `config.listAccountIds(cfg)` - List all configured accounts
- `config.resolveAccount(cfg, accountId)` - Get account settings
- `config.defaultAccountId(cfg)` - Default when not specified

### Security Model
- **DM Policy**: `pairing` (require approval), `open`, `deny`
- **Group Policy**: `allowlist`, `open`, `deny`
- **AllowFrom**: Explicit user/group allowlists
- **Mention Gating**: Require @mention in groups

---

## 4. The Skills System

Skills extend agent capabilities via workspace files.

### Skill Structure
A skill lives in `skills/<name>/SKILL.md`:
```markdown
---
name: sag
description: ElevenLabs text-to-speech
metadata: {
  "moltbot": {
    "emoji": "🗣️",
    "requires": { "bins": ["sag"], "env": ["ELEVENLABS_API_KEY"] },
    "install": [{ "id": "brew", "kind": "brew", "formula": "..." }]
  }
}
---

# sag

Use `sag` for ElevenLabs TTS...
```

### Skill Loading (`src/agents/skills/workspace.ts`)
Skills are loaded from multiple directories (priority order):
1. **Workspace skills** - `<workspace>/skills/`
2. **Managed skills** - `~/.config/moltbot/skills/`
3. **Extra dirs** - `skills.load.extraDirs` in config
4. **Plugin skills** - From loaded extensions
5. **Bundled skills** - Shipped with Moltbot

### Skill Selection at Runtime
The system prompt includes an `<available_skills>` block. The agent:
1. Scans skill descriptions
2. If one clearly applies, reads its `SKILL.md`
3. Follows the instructions

### Skill Metadata (Frontmatter)
```typescript
type ParsedSkillFrontmatter = {
  name: string;
  description?: string;
  homepage?: string;
  metadata?: {
    moltbot?: {
      emoji?: string;
      requires?: { bins?: string[]; env?: string[] };
      install?: SkillInstallSpec[];
      invocation?: "auto" | "manual" | "disabled";
    };
  };
};
```

### Hot Reloading (`src/agents/skills/refresh.ts`)
Skills are watched for changes:
```typescript
chokidar.watch(watchPaths, { ignoreInitial: true })
  .on("change", () => bumpSkillsSnapshotVersion({ reason: "watch" }));
```

---

## 5. The Memory System

The memory system (`src/memory/`) provides semantic search over workspace files and session transcripts.

### Architecture
```
┌─────────────────────────────────────────────────┐
│              MemoryIndexManager                 │
│  (src/memory/manager.ts)                        │
├─────────────────────────────────────────────────┤
│  Sources:                                       │
│  - memory/*.md files (workspace)                │
│  - Session transcripts                          │
├─────────────────────────────────────────────────┤
│  Indexes:                                       │
│  - SQLite FTS5 (keyword search)                 │
│  - sqlite-vec (vector similarity)              │
├─────────────────────────────────────────────────┤
│  Embedding Providers:                           │
│  - OpenAI (text-embedding-3-small)              │
│  - Gemini (text-embedding-004)                  │
│  - Local (node-llama-cpp)                       │
└─────────────────────────────────────────────────┘
```

### Key Components

**Chunking** (`internal.ts`):
- Markdown files split into chunks (~500 tokens)
- Preserves heading hierarchy for context

**Embeddings** (`embeddings.ts`):
- Provider auto-selection (prefers API keys you have)
- Fallback chain: OpenAI → Gemini → Local
- Batch processing for efficiency

**Hybrid Search** (`hybrid.ts`):
- Combines BM25 (keyword) + vector similarity
- Reciprocal rank fusion for final scores

### Agent Tools
- `memory_search` - Search across all memory files
- `memory_get` - Retrieve specific line ranges

### Sync Process
```typescript
// Files watched for changes
chokidar.watch(memoryDir)
  .on("change", () => manager.markDirty());

// Session transcripts synced incrementally
onSessionTranscriptUpdate((sessionKey) => {
  manager.markSessionDirty(sessionKey);
});
```

---

## 6. Notable Design Decisions

### 1. Plugin Architecture
Everything is a plugin - channels, tools, providers. This allows:
- External extensions (`extensions/`)
- Easy addition of new channels
- Clean separation of concerns

### 2. Session Key Hierarchy
The `agent:agentId:...` key structure enables:
- Multi-agent deployments
- Per-channel session isolation
- Thread support without collision

### 3. Gateway as Central Hub
The gateway pattern means:
- Single source of truth for state
- CLI, mobile app, web UI all connect the same way
- Hot reload without dropping connections

### 4. Tool Policies Compose
Multiple policy layers stack:
```
globalPolicy → providerPolicy → agentPolicy → groupPolicy → subagentPolicy
```
This allows fine-grained control without complexity at each level.

### 5. Skills are Just Markdown
No special DSL - skills are markdown files the agent reads. Benefits:
- Easy to write and share
- Agent can understand and follow naturally
- Frontmatter for machine-readable metadata

### 6. Subagent System
Spawning subagents for complex tasks:
- Isolated session with its own context
- Reports back to parent when done
- Configurable cleanup (delete or keep)

### 7. Cron + Heartbeat Dual System
- **Cron** (`src/cron/`): Precise scheduling, isolated sessions
- **Heartbeat** (`src/infra/heartbeat-runner.ts`): Periodic polls, uses main session
- Use heartbeat for "check things" tasks, cron for "do X at exactly Y time"

### 8. Channel Security is Multi-Layered
```
DM Policy → AllowFrom → Pairing Approval → Rate Limits
Group Policy → Group Allowlist → Mention Gating → Member Check
```

### 9. The Dock Pattern
`src/channels/dock.ts` provides lightweight channel utilities without importing heavy plugin code. This avoids circular dependencies and keeps startup fast.

### 10. Config Hot Reload
Config changes can be applied without restart:
```typescript
gateway.configReload.applyConfig(newConfig);
// Channels reconnect, tools update, policies refresh
```

---

## Key Files Reference

| Component | Location |
|-----------|----------|
| Gateway entry | `src/gateway/server.impl.ts` |
| Agent runner | `src/agents/pi-embedded-runner/run.ts` |
| Tool definitions | `src/agents/pi-tools.ts` |
| System prompt | `src/agents/system-prompt.ts` |
| Session management | `src/gateway/session-utils.ts` |
| Channel plugin type | `src/channels/plugins/types.plugin.ts` |
| Skills loader | `src/agents/skills/workspace.ts` |
| Memory manager | `src/memory/manager.ts` |
| Session keys | `src/routing/session-key.ts` |
| Cron types | `src/cron/types.ts` |
| Heartbeat runner | `src/infra/heartbeat-runner.ts` |
| Config schema | `src/config/zod-schema.ts` |

---

*This is me understanding myself. Pretty meta.*
