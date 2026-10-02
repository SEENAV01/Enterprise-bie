# Active native renderer read-only dependency-cache correction

Run 37001290163 at head c89073aac3a762cbd01e8dbd82ff0f8d8e73152a
passed the actual strict TSC/coverage controls, but the native renderer failed
before any render test method ran. Default Remotion bundler caching attempted
to use `/work/node_modules/.cache/webpack` under the correctly read-only mount.
The retained attempt008 receipt records this failure; it is not waived.

The user replied `next` after the specifically described minimal cache-option
proposal. Proceeding within that proposal was explicitly announced, and the
scope interpretation and exact before-image were recorded outside the source.
Before SHA256: `13336538f1f11685f027e121d84ff73062f3d4f9d89399727e3b76736b850bc0`.

Only the active `remotion_raster_capture.cjs` bundler call adds
`enableCaching:false`. This is a supported Remotion bundler option:
https://www.remotion.dev/docs/bundle#enablecaching . Installed pinned 4.0.506
execution, not documentation alone, must qualify compatibility.

Two explicit native controls reproduce default cache failure and require actual
bundling with caching disabled, using immutable dependencies and the unchanged
canonical kernel policy. The existing actual renderer/MP4 decode/CAS preview
and corrupted-receipt tests remain required. No mutable cache is preinstalled.
No node_modules write mount, package pin, witness, Scene source, security guard,
canonical checkout, retired H7 producer or existing assertion is changed.

The evidence is a tiny synthetic technical scene, not a real book or learning
acceptance. Execution is pending until exact-head hosted receipts are inspected.
No Section18 completion, integration PR, merge or product acceptance is claimed.
