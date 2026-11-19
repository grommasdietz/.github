# grommasdietz/.github

Shared GitHub Actions for Grommas Dietz Kirby plugins and websites. Each repository keeps a short caller workflow. The checks themselves stay in its own `composer verify` and `pnpm verify`, so local verification and CI run the same commands.

## Add CI to a plugin

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:

jobs:
  ci:
    uses: grommasdietz/.github/.github/workflows/kirby-plugin.yml@v1
    permissions:
      actions: write
      contents: write
      issues: write
      pull-requests: write
    with:
      release: ${{ vars.RELEASE_ENABLED == 'true' }}
      php: '8.3'
      compatibility: '[{"php": "8.2", "composer": "playground", "command": "composer test:smoke"}, {"php": "8.3", "kirby": "6.0.0-rc.3"}]'
    secrets: inherit
```

| Input                   | Default                 | Purpose                                                                                                                                                                                                                             |
| ----------------------- | ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `php`                   | `8.3`                   | PHP version for `composer verify`, `pnpm verify` and releases                                                                                                                                                                       |
| `extensions`            | common Kirby extensions | PHP extensions                                                                                                                                                                                                                      |
| `browsers`              | none                    | Playwright browsers installed before `pnpm verify`, for example `chromium webkit`                                                                                                                                                   |
| `apt`                   | none                    | Ubuntu packages installed before the checks, for example `imagemagick`                                                                                                                                                              |
| `compatibility`         | `[]`                    | JSON list of extra runs. Each entry takes `php` and optionally `kirby` (a version to require), `composer` (`all`, `playground` or `none`), `command`, `name`, `ref`, `node` and `browsers` (the check name defaults to `PHP <php>`) |
| `compatibility-command` | `composer test`         | Command for entries without their own `command`. Kirby runs also get `KIRBY_TEST_MAJOR`                                                                                                                                             |
| `release`               | `true`                  | Run Semantic Release on the default branch after all checks pass                                                                                                                                                                    |
| `dependabot-minor`      | `true`                  | Also merge eligible minor updates of stable packages. Set to `false` for patches only.                                                                                                                                              |

A Kirby override updates every existing CMS requirement in the selected Composer scope, including the playground used by integration tests. It does not add an unused second CMS to a root tooling manifest. Without an override, installs remain frozen to their lockfiles.

A compatibility entry can check a dedicated native Kirby 6 branch with `ref: "kirby-6"`, `node: true`, `browsers: "chromium"` and `command: "composer verify && pnpm verify"`. Give it a clear name such as `Kirby 6 branch`: this tests that branch's current commit, while the normal Verify job tests the calling push or pull request. Release and Dependabot jobs remain bound to the caller's default-branch verification.

Releases use the GitHub App from `vars.GD_RELEASE_BOT_CLIENT_ID` and `secrets.GD_RELEASE_BOT_PRIVATE_KEY` when configured, otherwise the workflow token. Gate publishing with `release: ${{ vars.RELEASE_ENABLED == 'true' }}` when a repository should not publish yet.

## Add CI to a website

```yaml
jobs:
  ci:
    uses: grommasdietz/.github/.github/workflows/kirby-site.yml@v1
    permissions:
      actions: write
      contents: write
      pull-requests: write
    with:
      php-extra: '8.4'
      bundle: ${{ vars.DEPLOY_ENABLED == 'true' }}
    secrets: inherit
```

The website workflow runs `pnpm verify` and `composer verify`.

| Input              | Default | Purpose                                                |
| ------------------ | ------- | ------------------------------------------------------ |
| `php`              | `8.3`   | PHP version for verification and packaging             |
| `php-extra`        | Empty   | Additional PHP version for Composer verification       |
| `bundle`           | `false` | Allow packaging on the default branch                  |
| `dependabot-minor` | `true`  | Allow eligible stable minor updates as well as patches |

| Event                                                | When does the job upload a bundle?                                                                                                   |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Pull request or non-default branch                   | Verification only                                                                                                                    |
| Default-branch push with bundling enabled            | A known diff limited to Markdown, `docs/` or `.github/` skips packaging. A code change or unavailable comparison triggers packaging. |
| Default-branch manual dispatch with bundling enabled | Packages the current revision when the dispatch has no previous commit to compare                                                    |
| Bundling disabled                                    | Verification only for every event                                                                                                    |

The `bundle` output is true after the `deploy-htdocs` upload succeeds. The website caller uses this output to start its **Staging** job. Check the server receipt before starting client review. See the [website workflow](.github/workflows/kirby-site.yml) and the [deployment runbook](https://github.com/grommasdietz/kirby-deploy/blob/v1/docs/runbook.md). Set `ENABLE_CRITICAL_CSS` and `CRITICAL_CSS_BASE_URL` when the site needs critical CSS.

## Shared behavior

- **Conventional Commits:** pull request titles and new commits are linted with the repository's commitlint configuration. Dependabot is exempt.
- **Workflows:** Actionlint validates every workflow.
- **Dependabot:** after all checks pass in the same run, patch updates and minor updates of stable packages are squash-merged. Majors, pre-1.0 minors and pre-releases stay open for review. Set `dependabot-minor: false` to merge only patches automatically. The default branch is then verified again by dispatching the caller workflow, which needs a `workflow_dispatch` trigger.
- **Private packages:** `secrets.GH_COMPOSER_TOKEN` authenticates private Composer packages. Add it as an Actions secret and as a Dependabot secret.

## Review documentation changes

Run the shared punctuation rule from the repository you are editing. Point `GD_DOCS_TOOLS` at the `tools` directory of your local checkout of this repository. Use the base commit of the change you want to review.

```sh
GD_PROSE_BASE=HEAD npx --yes markdownlint-cli@0.50.0 --config "$GD_DOCS_TOOLS/markdown-prose.json" --rules "$GD_DOCS_TOOLS/markdown-prose.cjs" -- README.md 'docs/**/*.md'
```

With `HEAD`, the rule checks working changes and new files in the supplied paths. For a branch review, set the base to its merge base. Omit the variable to review whole files. Select studio-authored guides and policies. Keep verbatim quotations, license terms, released changelogs and upstream copies outside the editing pass. The rule skips Markdown code and link destinations. Review installation examples against the branch manifests and shared workflow examples against their declared inputs.

## Changing these workflows

Callers use the moving `v1` tag. Run `actionlint` and Prettier before pushing, test changes from a branch in one caller with `@<branch>`, then move the tag with `git tag -f v1 && git push -f origin v1`. Breaking input changes get a new major tag.
