#!/bin/bash
# Fetches the third-party source code STRATUM compiles in, pinned to the commits it was built against:
# Steinberg's VST3 SDK (MIT licence) and Airwindows Consolidated (MIT licence).
set -euo pipefail
cd "$(dirname "$0")"
sdk() {
  [ -d "vendor/vst3sdk/$1" ] && return
  git clone -q "https://github.com/steinbergmedia/$2.git" "vendor/vst3sdk/$1"
  git -C "vendor/vst3sdk/$1" checkout -q "$3"
}
mkdir -p vendor/vst3sdk
sdk pluginterfaces vst3_pluginterfaces 4f547e8e102b47de4a8b8aaf343c73b700786372
sdk base vst3_base fcf9da0bd27a16f7f03773a3a39822f28f5c8477
sdk public.sdk vst3_public_sdk 586dc5e6c8012c3e4b01c79389375cbe96bdb1da
if [ ! -d vendor/airwin2rack ]; then
  git clone -q https://github.com/baconpaul/airwin2rack.git vendor/airwin2rack
  git -C vendor/airwin2rack checkout -q 8a67b80e04230a5cf40e84d6e8b9a2fd70b13a75
fi
# ONNX Runtime for Windows (MIT licence), for stem separation in the Windows app. Only fetched on Windows.
# It comes from Microsoft's official NuGet package (the GitHub release download stopped working in November 2026), checked
# against the SHA-512 NuGet publishes, and is laid out as the GitHub zip was: include/, lib/onnxruntime.dll, licences.
ORT_WIN=vendor/onnxruntime-win-x64-1.31.0
if [ "${OS:-}" = "Windows_NT" ] && [ ! -f "$ORT_WIN/lib/onnxruntime.dll" ]; then
  curl -fsSL --retry 3 -o vendor/ort-win.nupkg https://api.nuget.org/v3-flatcontainer/microsoft.ml.onnxruntime/1.31.0/microsoft.ml.onnxruntime.1.31.0.nupkg
  python - vendor/ort-win.nupkg <<'PY'
import base64, hashlib, sys
h = base64.b64encode(hashlib.sha512(open(sys.argv[1], 'rb').read()).digest()).decode()
want = 'J7arTn+7nrWdZ+PF2Sl9aNW1/Ba5DCt1ywZ3r5l3LKqzj3w8oC7Cl/uagG3Xp1ivuYJYQAMSuew0ef/74f7XCw=='
sys.exit(0 if h == want else 'ONNX Runtime package hash mismatch: ' + h)
PY
  rm -rf vendor/ort-pkg "$ORT_WIN" && mkdir -p vendor/ort-pkg "$ORT_WIN/include" "$ORT_WIN/lib"
  unzip -q vendor/ort-win.nupkg 'build/native/include/*' 'runtimes/win-x64/native/*' LICENSE ThirdPartyNotices.txt -d vendor/ort-pkg
  cp vendor/ort-pkg/build/native/include/* "$ORT_WIN/include/"
  cp vendor/ort-pkg/runtimes/win-x64/native/* "$ORT_WIN/lib/"
  cp vendor/ort-pkg/LICENSE vendor/ort-pkg/ThirdPartyNotices.txt "$ORT_WIN/"
  rm -rf vendor/ort-pkg vendor/ort-win.nupkg
fi
echo "Vendor code ready."
