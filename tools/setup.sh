#!/usr/bin/env bash
# 음성 생성 환경 준비. 모델은 GitHub Releases(k2-fsa/sherpa-onnx)에서 받음. 이미 있으면 건너뜀.
set -e
M="${MODELS_DIR:-$HOME/hsk-models}"; mkdir -p "$M"; cd "$M"
REL="https://github.com/k2-fsa/sherpa-onnx/releases/download"
get(){ # url, outfile
  [ -s "$2" ] || curl -sSL --retry 3 --max-time 900 -o "$2" "$1"; }
untar(){ [ -d "$2" ] || tar xjf "$1"; }
pip install --break-system-packages -q sherpa-onnx soundfile librosa pypinyin jieba numpy 2>&1 | grep -v -i warning || true
# 엔진C: ZipVoice (음성 복제, 자연스러움) + 24kHz 보코더
get "$REL/tts-models/sherpa-onnx-zipvoice-distill-int8-zh-en-emilia.tar.bz2" zv.tar.bz2; untar zv.tar.bz2 sherpa-onnx-zipvoice-distill-int8-zh-en-emilia
get "$REL/tts-models/sherpa-onnx-zipvoice-distill-zh-en-emilia.tar.bz2" zvf.tar.bz2; untar zvf.tar.bz2 sherpa-onnx-zipvoice-distill-zh-en-emilia   # fp32 (고음질)
get "$REL/vocoder-models/vocos_24khz.onnx" vocos_24khz.onnx
get "$REL/tts-models/lexicon-en-us.txt" lexicon-en-us.txt
# 엔진B: Matcha baker (또박또박, 빠름) + 22kHz 보코더
get "$REL/tts-models/matcha-icefall-zh-baker.tar.bz2" matcha.tar.bz2; untar matcha.tar.bz2 matcha-icefall-zh-baker
get "$REL/vocoder-models/vocos-22khz-univ.onnx" vocos-22khz-univ.onnx
# 자가검수용 음성인식 (SenseVoice)
get "$REL/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17.tar.bz2" sv.tar.bz2; untar sv.tar.bz2 sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17
which ffmpeg >/dev/null || (apt-get install -y -q ffmpeg >/dev/null 2>&1 || true)
echo "models ready in $M"
