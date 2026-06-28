# sync-fork

自动同步上游仓库的 tags 和分支到你的 fork。

本仓库同时提供两种使用方式：

- **方案 A（单仓库）**：在每个 fork 里放一份 workflow，调用 `SourceDive/sync-fork` action
- **方案 B（中心化）**：在本仓库用 `sync-all-forks.yml` 统一调度所有 fork（推荐）

## 前置条件

**必须使用 Classic Personal Access Token（用户 PAT），不能用 GitHub App token 或默认 GITHUB_TOKEN。**

创建 Classic PAT：https://github.com/settings/tokens/new?scopes=repo,workflow

勾选权限：
- `repo`（完整仓库权限）
- `workflow`（修改 workflow 文件，同步含 workflow 的 release tag 必需）

> 错误示例：`refusing to allow a GitHub App to create or update workflow ... without workflows permission`
> 说明当前 token 不是带 workflow 权限的 Classic PAT。

存入 Organization Secret `SYNC_FORK_TOKEN`，并确保 `fork-sync-hub` 仓库有权访问该 Secret。

Settings → Secrets and variables → Actions → New organization secret

## 方案 B：中心化同步所有 Fork（推荐）

本仓库已配置 `.github/workflows/sync-all-forks.yml`，会读取 `forks.json` 中的矩阵配置，每天自动同步所有 fork。

### 首次启用

1. 在 Organization 或本仓库配置 `SYNC_FORK_TOKEN`
2. 确认 `forks.json` 包含你要同步的 fork 列表
3. 到 Actions 页手动触发 **Sync All Forks** 验证

### 新增 Fork 后

运行脚本重新生成配置：

```bash
python3 scripts/generate-forks-config.py
git add forks.json
git commit -m "chore: update forks.json"
git push
```

或手动在 `forks.json` 追加一条：

```json
{
  "fork": "SourceDive/your-repo",
  "upstream": "owner/upstream-repo",
  "target_branch": "main"
}
```

### 手动触发选项

- `fork_filter`：只同步名称匹配的 fork（如 `spring-ai`）
- `sync_tags` / `sync_branches`：控制同步内容
- `skip_workflow_tags_on_error`：临时跳过因 workflow 权限失败的 tag（根治方案仍是更换正确 PAT）

## 故障排查

| 错误 | 原因 | 解决 |
|------|------|------|
| `without workflows permission` | token 是 GitHub App 或缺少 workflow scope | 换 Classic PAT，勾选 `repo` + `workflow` |
| `SYNC_FORK_TOKEN 未配置` | Secret 未设置或仓库无权访问 | 在 Organization 配置并授权 fork-sync-hub |
| 分支同步成功但 tag 失败 | 仅 tag 含 workflow 文件变更 | 同上，必须 workflow 权限 |

### 启用中心化后

各 fork 仓库里的 `.github/workflows/sync-fork.yml` 可以删除，避免重复同步。

## 方案 A：单仓库同步

将 `templates/sync-fork.yml` 复制到 fork 仓库的 `.github/workflows/` 目录，修改 `upstream_repo`：

```yaml
name: Sync Fork from Upstream
on:
  schedule:
    - cron: '0 0 * * *'
  workflow_dispatch:
jobs:
  sync:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      actions: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: SourceDive/sync-fork@v1.1
        with:
          upstream_repo: spring-projects/spring-ai
          github_token: ${{ secrets.SYNC_FORK_TOKEN }}
          sync_tags: 'true'
          sync_branches: 'true'
          target_branch: main
```

## Action 参数

| 参数 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `upstream_repo` | 是 | — | 上游仓库，格式 `owner/repo` |
| `github_token` | 是 | — | PAT，需 `repo` + `workflow` 权限 |
| `sync_tags` | 否 | `true` | 是否同步 tags |
| `sync_branches` | 否 | `false` | 是否同步分支 |
| `target_branch` | 否 | `main` | 要同步的分支，多个用逗号分隔 |
