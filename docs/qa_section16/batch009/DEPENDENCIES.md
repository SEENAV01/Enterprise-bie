# Dependency boundaries

The cumulative archive preserves previously delivered QA/native dependencies.
New native ANI files were read through GitHub at commit
375d99af0edd0086206817dae932156ddf61c569; native_dependencies_009.json records exact
Git blob SHA1, byte SHA256 and lengths. No current-HEAD adoption is implied.

Core animation contracts/metrics/reviews use Python standard library plus inherited
BIE modules. PNG validation uses Pillow. Structural-schema tests use jsonschema.
Browser diagnostics use Python Playwright and /usr/bin/chromium by default; the
collector exposes executable_path for explicitly configured deployments. This
package neither downloads binaries nor embeds executable browsers or font files.
Executed versions are recorded, not asserted as the latest or universally supported.
