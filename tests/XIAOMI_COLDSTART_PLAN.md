# Xiaomi CPU and cold-start test

## Why CPU is blank

Android9 Xiaomi5925 denies `/proc/stat` and `cpuinfo` to the ordinary launcher UID. The old `dumpsys cpuinfo` route also failed for an app and was removed. Showing only our own process load as total CPU would be false. A shell UID has access, so this test collects aggregate system CPU from read-only `dumpsys cpuinfo` while connected over already-authorized ADB. This will diagnose load; it will not make a permanent TV widget by itself.

## Preparation and safety

1. Verify `MiTV-MSSP1/nino`, IP `192.168.18.144:5555`, ADB authorization and local output directory. The runner stops if model/device differ.
2. Keep Aerial Views, Home/Google, voice, tuner, VPN, installed apps and settings unchanged. Do not clear caches/data or disable packages during the experiment.
3. Run `python3 scripts/xiaomi-coldstart-test.py --adb /Users/roman/Library/Android/sdk/platform-tools/adb --port 5038 --output reports/xiaomi-deep-optimization-20261110/private/coldstart-NN`. It captures one baseline, then waits for the operator to fully power off/on using the physical remote. It does not issue reboot/power commands. `NN` is a new empty directory for each run.
4. The user confirms the TV has fully powered off before pressing Enter. After ADB returns, samples are scheduled against one monotonic boot-ready origin at +0s, +60s, +180s and +300s. Each point runs `top -n 1` twice as separate commands with a five-second gap; compare those two outputs. Keep room conditions, network, attached HDMI devices and remote use constant; do not open streaming apps during this series.

## Captured signals

At each point: `dumpsys cpuinfo`, RAM/swap, two independent `top` snapshots, PSS, active services, current window, free storage, boot-complete state and UTC timestamp. `dumpsys cpuinfo` may report a CPU interval that is stale or misaligned on this firmware; compare its reported interval to the host timestamp and do not use it as the sole point-in-time metric. Compare the separate `top` outputs; a single output does not prove sustained use. The runner retains only the requested bounded text outputs; no logcat, account data, keystrokes, speech, screen content, or app data is read. Source of truth is each JSON sample, not an aggregated dashboard.

## Interpretation

- Compare `top` CPU percentages and process ranks across all four times, not `Load` averages. The first collector run (`coldstart-01`) used incorrect relative delays and single-report `top`; its labels +180/+300 were not true boot elapsed times and `dumpsys cpuinfo` intervals were misaligned. The second run (`coldstart-02`) used correct sample timing, but Android `top -n 2` repeated identical output; do not treat those two blocks as independent measurements. A follow-up used separate `top -n 1` commands while Aerial Views was active and found sustained load; see the results report.
- Distinguish short boot work from persistent load. Attribute heat only if sensor data is available; this runner does not infer temperature.
- Check foreground window and services before calling a process causal. `media.codec` can be normal video decode; do not disable it. PatchWall should be considered only if its package/process actually exists and is measurably active.
- Memory pressure: compare MemAvailable and SwapFree across times. Low free RAM alone is not a fault because file cache is reclaimable.
- No packages or settings are changed. Repeat a second cold start only if the first series is complete and no TV fault occurs.
- After analysis, propose one reversible change at a time and capture the same sequence for before/after comparison. Do not call a change successful based on one boot.
