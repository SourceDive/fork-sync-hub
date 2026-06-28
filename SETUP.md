# 部署指南

本目录是方案 B 的完整中心化同步 Hub，应部署到独立仓库 `SourceDive/fork-sync-hub`。

## 1. 创建仓库

在 GitHub 上新建空仓库：

- 名称：`fork-sync-hub`
- Organization：`SourceDive`
- 不要初始化 README

## 2. 推送本目录内容

```bash
cd fork-sync-hub
git init
git add .
git commit -m "feat: centralized fork sync hub"
git branch -M main
git remote add origin https://github.com/SourceDive/fork-sync-hub.git
git push -u origin main
```

## 3. 配置 Secret

在 Organization `SourceDive` 级别创建 Secret：

- 名称：`SYNC_FORK_TOKEN`
- 值：**Classic PAT**（不是 GitHub App），权限勾选 `repo` + `workflow`
- 创建链接：https://github.com/settings/tokens/new?scopes=repo,workflow
- 确保 `fork-sync-hub` 在 Organization Secret 的仓库访问列表中

Organization Secret 会自动被本仓库及所有 fork 使用。

## 4. 启用同步

1. 打开 `SourceDive/fork-sync-hub` → Actions
2. 手动触发 **Sync All Forks** 验证
3. 确认成功后，可删除各 fork 仓库里的 `.github/workflows/sync-fork.yml`（避免重复同步）

## 5. 新增 Fork 后

```bash
python3 scripts/generate-forks-config.py
git add forks.json && git commit -m "chore: update forks.json" && git push
```
