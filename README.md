# grommasdietz/.github

Shared GitHub Actions for Grommas Dietz Kirby plugins and websites. Each repository keeps a short caller workflow; the checks themselves stay in its own `composer verify` and `pnpm verify`, so local verification and CI run the same commands.

## Plugins

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
      php: '8.3'
      compatibility: '[{"php": "8.2", "composer": "playground", "command": "composer test:smoke"}, {"php": "8.3", "kirby": "6.0.0-beta.3"}]'
    secrets: inherit
```

| Input                   | Default                 | Purpose                                                                                                                                                                                               |
| ----------------------- | ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `php`                   | `8.3`                   | PHP version for `composer verify`, `pnpm verify` and releases                                                                                                                                         |
| `extensions`            | common Kirby extensions | PHP extensions                                                                                                                                                                                        |
| `browsers`              | none                    | Playwright browsers installed before `pnpm verify`, for example `chromium webkit`                                                                                                                     |
| `apt`                   | none                    | Ubuntu packages installed before the checks, for example `imagemagick`                                                                                                                                |
| `compatibility`         | `[]`                    | JSON list of extra runs. Each entry takes `php` and optionally `kirby` (a version to require), `composer` (`all`, `playground` or `none`), `command` and `name` (the check name, default `PHP <php>`) |
| `compatibility-command` | `composer test`         | Command for entries without their own `command`. Kirby runs also get `KIRBY_TEST_MAJOR`                                                                                                               |
| `release`               | `true`                  | Run Semantic Release on the default branch after all checks pass                                                                                                                                      |

Releases use the GitHub App from `vars.GD_RELEASE_BOT_CLIENT_ID` and `secrets.GD_RELEASE_BOT_PRIVATE_KEY` when configured, otherwise the workflow token. Gate publishing with `release: ${{ vars.RELEASE_ENABLED == 'true' }}` when a repository should not publish yet.

## Websites

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

The job runs `pnpm verify`, then `composer verify`, and repeats `composer verify` on `php-extra`. With `bundle` enabled, pushes to the default branch that change more than documentation or `.github/` upload the `deploy-htdocs` artifact for [kirby-deploy](https://github.com/grommasdietz/kirby-deploy) and set the `bundle` output. `vars.ENABLE_CRITICAL_CSS` and `vars.CRITICAL_CSS_BASE_URL` keep the optional critical CSS step.

## Shared behavior

- **Conventional Commits:** pull request titles and new commits are linted with the repository's commitlint configuration. Dependabot is exempt.
- **Workflows:** Actionlint validates every workflow.
- **Dependabot:** after all checks pass in the same run, patch updates and minor updates of stable packages are squash-merged. Majors, pre-1.0 minors and pre-releases stay open for review. The default branch is then verified again by dispatching the caller workflow, which needs a `workflow_dispatch` trigger.
- **Private packages:** `secrets.GH_COMPOSER_TOKEN` authenticates private Composer packages. Add it as an Actions secret and as a Dependabot secret.

## Changing these workflows

Callers use the moving `v1` tag. Run `actionlint` and Prettier before pushing, test changes from a branch in one caller with `@<branch>`, then move the tag with `git tag -f v1 && git push -f origin v1`. Breaking input changes get a new major tag.
