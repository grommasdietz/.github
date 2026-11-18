#!/usr/bin/env bash
set -euo pipefail

flags=(--no-interaction --prefer-dist --no-progress)
: "${SCOPE:=all}"
: "${KIRBY:=}"

if [[ -n "$KIRBY" ]]; then
  major="$(php -r 'preg_match("/[0-9]+/", getenv("KIRBY"), $match); echo $match[0] ?? "";')"
  printf 'KIRBY_TEST_MAJOR=%s\n' "$major" >> "${GITHUB_ENV:?}"
fi

install_scope() {
  local directory="$1" requirement
  local development=(require)
  requirement="$(php -r '
    $data = json_decode(file_get_contents($argv[1]), true, 512, JSON_THROW_ON_ERROR);
    echo isset($data["require"]["getkirby/cms"]) ? "runtime" :
      (isset($data["require-dev"]["getkirby/cms"]) ? "development" : "none");
  ' "$directory/composer.json")"
  if [[ -z "$KIRBY" || "$requirement" == none ]]; then
    composer --working-dir="$directory" install "${flags[@]}"
    return
  fi
  if [[ "$requirement" == development ]]; then development+=(--dev); fi
  composer --working-dir="$directory" config platform.php "$(php -r 'echo PHP_VERSION;')"
  composer --working-dir="$directory" "${development[@]}" "getkirby/cms:$KIRBY" \
    --with-all-dependencies --no-scripts "${flags[@]}"
}

if [[ -f playground/composer.json ]]; then
  install_scope playground
elif [[ "$SCOPE" == playground ]]; then
  echo 'The playground Composer scope requires playground/composer.json.' >&2
  exit 1
fi
if [[ "$SCOPE" != playground ]]; then install_scope .; fi
