# fork-sync-hub

自动同步上游仓库的 tags 和分支到你的 fork。

本仓库是**单一来源**：既是可复用的 Composite Action，也是中心化调度 Hub。原 `SourceDive/sync-fork` 独立仓库已统一合并到这里，不再单独维护两个仓库。

提供两种使用方式：

- **方案 A（单仓库）**：在每个 fork 里放一份 workflow，调用本仓库 action `SourceDive/fork-sync-hub@v1`
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

本仓库已配置 `.github/workflows/sync-all-forks.yml`，会读取 `forks.json` 中的矩阵配置，每天自动同步所有 fork。它直接复用本仓库根目录的 `action.yml`。

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
- `tag_force`：是否强制覆盖 fork 上已存在的同名 tag
- `branch_sync_mode`：分支同步方式（`force` 用上游覆盖 / `merge` 或 `rebase` 保留 fork 自有提交）

> 定时任务默认按**镜像**语义运行（`tag_force=true`、`branch_sync_mode=force`），即用上游覆盖 fork。如需保留 fork 自有提交，请手动触发并选择 `merge`/`rebase`。

### 启用中心化后

各 fork 仓库里的 `.github/workflows/sync-fork.yml` 可以删除，避免重复同步。

## 方案 A：单仓库同步

将 `templates/sync-fork.yml` 复制到 fork 仓库的 `.github/workflows/` 目录，修改 `UPSTREAM_REPO`：

```yaml
name: Sync Fork from Upstream
on:
  schedule:
    - cron: '0 0 * * *'
  workflow_dispatch:

concurrency:
  group: sync-fork-${{ github.ref }}
  cancel-in-progress: false

jobs:
  sync:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      actions: write
    steps:
      - uses: actions/checkout@v5
        with:
          fetch-depth: 0
      - uses: SourceDive/fork-sync-hub@v1
        with:
          upstream_repo: spring-projects/spring-ai
          github_token: ${{ secrets.SYNC_FORK_TOKEN }}
          sync_tags: 'true'
          sync_branches: 'true'
          target_branch: main
```

> 启用分支同步（`merge`/`rebase` 模式）时，请务必保留 `fetch-depth: 0`，否则无法获得完整历史。

## Action 参数

| 参数 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `upstream_repo` | 是 | — | 上游仓库，格式 `owner/repo` |
| `github_token` | 是 | — | PAT，需 `repo` + `workflow` 权限 |
| `sync_tags` | 否 | `true` | 是否同步 tags |
| `tag_force` | 否 | `false` | 推送 tags 时是否强制覆盖 fork 上同名 tag |
| `sync_branches` | 否 | `false` | 是否同步分支 |
| `target_branch` | 否 | （空）| 要同步的分支，多个用逗号分隔；留空则自动探测上游默认分支 |
| `branch_sync_mode` | 否 | `merge` | 分支同步方式：`merge` / `rebase` / `force` |
| `git_user_name` | 否 | `github-actions[bot]` | `merge`/`rebase` 生成提交所用用户名 |
| `git_user_email` | 否 | `...github-actions[bot]...` | `merge`/`rebase` 生成提交所用邮箱 |
| `working_directory` | 否 | `.` | fork 仓库的本地路径（中心化调度时指向 fork 检出目录） |

## 分支同步说明

- `merge`（默认）/ `rebase`：把上游合并进 fork 的同名分支，**保留 fork 自己的提交**；若产生冲突会让任务失败而不是静默覆盖。
- `force`：用上游分支强制覆盖 fork 同名分支，会**丢弃 fork 上的自有提交**（适合纯镜像场景，中心化定时任务默认采用）。

## 故障排查

| 错误 | 原因 | 解决 |
|------|------|------|
| `without workflows permission` | token 是 GitHub App 或缺少 workflow scope | 换 Classic PAT，勾选 `repo` + `workflow` |
| `SYNC_FORK_TOKEN 未配置` | Secret 未设置或仓库无权访问 | 在 Organization 配置并授权 fork-sync-hub |
| 分支同步成功但 tag 失败 | 仅 tag 含 workflow 文件变更 | 同上，必须 workflow 权限 |
| `merge`/`rebase` 报历史不完整 | checkout 缺少 `fetch-depth: 0` | 在 checkout 步骤加上 `fetch-depth: 0` |
