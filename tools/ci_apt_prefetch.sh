# Task 045 / F-11(a): bounded apt downloads with one fail-over to the runner
# image's own next mirror. Sourced by .integration/tools/setup_ci_environment.sh.
#
# Evidence: on hosted runners, .deb downloads from the regional mirror
# (azure.archive.ubuntu.com) crawled at 45-104 kB/s (PR #48 run 39890973906,
# PR #53 run 39986108672) while a healthy run fetches the same 95 MB in 5 s, so
# provisioning hit the 20-minute job limit before any test ran. apt-get has no
# minimum-speed limit (Acquire::*::Timeout only catches a stalled connection).
#
# apt_prefetch only DOWNLOADS (apt-get --download-only); the unchanged install
# commands then install from the local cache. Package set, versions and trust
# are unchanged: apt verifies every .deb against the signed archive indexes,
# and the fail-over drops the regional line of the image's own mirror list. When
# the image lists ONLY the regional mirror (18 November 2026, PR #166: two runs an
# hour apart, "no second mirror listed"), the fail-over points the regional host
# at Ubuntu's primary archive (archive.ubuntu.com, the same signed indexes and the
# same Ubuntu archive key) wherever apt names it: the mirror list, sources.list,
# *.list or deb822 *.sources files; nothing else in apt's sources or trust
# changes. Navin said yes on 18 November 2026. Every fail-over first writes a
# ::notice listing where apt fetches from, because job logs cannot be read here.
# Worst case for all prefetches of one job: APT_BUDGET_S seconds, then a clear
# ::error annotation and a non-zero exit instead of a silent job cancel.

APT_MIRRORS="${APT_MIRRORS:-/etc/apt/apt-mirrors.txt}"
APT_BUDGET_S="${APT_BUDGET_S:-480}"        # all prefetches of this job together
APT_FIRST_TRY_S="${APT_FIRST_TRY_S:-180}"  # first try on the regional mirror (healthy: ~10 s)
APT_REGIONAL='^http://azure\.archive\.ubuntu\.com/'
APT_SLOW_HOST='([a-z0-9-]+\.)*azure\.archive\.ubuntu\.com'   # the runner's regional mirror, any region prefix
APT_PRIMARY_HOST='archive.ubuntu.com'
APT_SOURCES_DIR="${APT_SOURCES_DIR:-/etc/apt}"
APT_FAILED_OVER=0
APT_DEADLINE=$((SECONDS + APT_BUDGET_S))

apt_get_bounded() {  # <seconds> <apt-get arguments...>
  local seconds="$1"; shift
  sudo timeout --kill-after=15 "$seconds" apt-get -q -o Acquire::Retries=3 \
    -o Acquire::http::Timeout=30 -o Acquire::https::Timeout=30 "$@"
}

apt_sources_summary() {  # one line for the annotation: where apt fetches from (URLs only, no secrets live here)
  local f
  { test -f "$APT_MIRRORS" && sed -n 's#^\(https\{0,1\}://[^[:space:]]*\).*#mirror-list \1#p' "$APT_MIRRORS"
    for f in "$APT_SOURCES_DIR"/sources.list "$APT_SOURCES_DIR"/sources.list.d/*.list "$APT_SOURCES_DIR"/sources.list.d/*.sources; do
      test -f "$f" || continue
      grep -Eho '(mirror\+file:[^[:space:]]+|https?://[^[:space:]]+)' "$f" | sed "s#^#${f##*/} #"
    done; } 2>/dev/null | sort -u | head -12 | tr '\n' ';' | cut -c1-900
}

apt_slow_host_files() {  # the apt source files (mirror list, sources.list, *.list, deb822 *.sources) naming the regional host
  local f
  for f in "$APT_MIRRORS" "$APT_SOURCES_DIR"/sources.list "$APT_SOURCES_DIR"/sources.list.d/*.list "$APT_SOURCES_DIR"/sources.list.d/*.sources; do
    if test -f "$f" && grep -Eq "https?://${APT_SLOW_HOST}/" "$f"; then echo "$f"; fi
  done
}

apt_mirror_failover() {
  local left files f
  APT_FAILED_OVER=1
  echo "::notice title=APT sources (F-11)::$(apt_sources_summary)"
  if test -f "$APT_MIRRORS" && grep -q "$APT_REGIONAL" "$APT_MIRRORS" && grep -vq "$APT_REGIONAL" "$APT_MIRRORS"; then
    echo "apt mirror list before fail-over:"; cat "$APT_MIRRORS"
    sudo sed -i '\#^http://azure\.archive\.ubuntu\.com/#d' "$APT_MIRRORS"
    echo "apt mirror list after fail-over:"; cat "$APT_MIRRORS"
    echo "::warning title=APT mirror fail-over (F-11)::regional mirror too slow; using the image's next listed mirror"
  else
    files=$(apt_slow_host_files)
    if test -z "$files"; then
      echo "::warning title=APT mirror fail-over (F-11)::no second mirror listed; retrying the same mirror"
      return 0
    fi
    for f in $files; do
      sudo sed -i -E "s#(https?)://${APT_SLOW_HOST}/#\\1://${APT_PRIMARY_HOST}/#g" "$f"
    done
    echo "::warning title=APT mirror fail-over (F-11)::regional mirror too slow and no second mirror listed; using Ubuntu's primary archive (${APT_PRIMARY_HOST}) in $(for f in $files; do printf '%s ' "${f##*/}"; done)"
  fi
  left=$((APT_DEADLINE - SECONDS))
  test "$left" -gt 0 || return 1
  apt_get_bounded "$((left < 90 ? left : 90))" update
}

apt_prefetch() {  # <apt-get install options and packages...>; downloads only, installs nothing
  local attempt left
  for attempt in 1 2; do
    left=$((APT_DEADLINE - SECONDS))
    test "$left" -gt 0 || break
    if test "$APT_FAILED_OVER" = 0 && test "$left" -gt "$APT_FIRST_TRY_S"; then left="$APT_FIRST_TRY_S"; fi
    if apt_get_bounded "$left" install -y --download-only "$@"; then return 0; fi
    if test "$attempt" != 1 || test "$APT_FAILED_OVER" != 0; then break; fi
    apt_mirror_failover || break
  done
  echo "::error title=APT download bound (F-11)::apt downloads did not finish within the ${APT_BUDGET_S} s budget"
  return 1
}

apt_packages_from_playwright_dry_run() {  # stdin: `playwright install-deps --dry-run` output
  python -I -c '
import re, sys
text = sys.stdin.read()
marker = "apt-get install -y --no-install-recommends "
if text.count(marker) != 1: raise SystemExit("PLAYWRIGHT_DEPS_FORMAT")
names = text.split(marker, 1)[1].split(chr(34), 1)[0].split()
if not names or any(not re.fullmatch(r"[a-z0-9][a-z0-9.+-]+", name) for name in names):
    raise SystemExit("PLAYWRIGHT_DEPS_FORMAT")
print(" ".join(names))'
}
