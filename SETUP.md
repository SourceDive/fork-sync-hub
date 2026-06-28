# 部署指南

本目录是统一后的同步 Hub，应部署到仓库 `SourceDive/fork-sync-hub`。它同时是可复用的 Composite Action（根目录 `action.yml`，供方案 A 通过 `SourceDive/fork-sync-hub@v1` 调用）和方案 B 的中心化调度 Hub。原 `SourceDive/sync-fork` 独立仓库已合并到此处。

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

## 6. 发布 Action 版本（方案 A 需要）

方案 A 的 fork 通过 `SourceDive/fork-sync-hub@v1` 引用本仓库根目录的 `action.yml`，因此需要发布并维护一个 `v1` 移动标签：

```bash
git tag -f v1
git push -f origin v1
```

每次更新 `action.yml` 后，将 `v1` 标签重新指向最新提交即可让所有方案 A 的 fork 生效。

## 7. 下线旧仓库 `SourceDive/sync-fork`

原独立 action 仓库已合并到此处。建议在其 README 顶部注明「已迁移到 `SourceDive/fork-sync-hub`」并归档（Archive）该仓库，避免两处维护。
