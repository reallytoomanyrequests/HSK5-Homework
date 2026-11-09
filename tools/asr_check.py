"""생성된 mp3를 음성인식으로 다시 받아써서 대본과 대조 (자가검수).
usage: python3 asr_check.py out.mp3 script.json   → 문자 일치율과 불일치 구간 출력. 일치율 90% 미만이면 exit 1
"""
import sys, os, json, re, difflib, subprocess
import numpy as np, soundfile as sf, sherpa_onnx
M=os.environ.get("MODELS_DIR",os.path.expanduser("~/hsk-models"))
A=f"{M}/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17"
rec=sherpa_onnx.OfflineRecognizer.from_sense_voice(model=f"{A}/model.int8.onnx",tokens=f"{A}/tokens.txt",use_itn=False,num_threads=os.cpu_count() or 4)
def asr(path):
    wav=path+".asr.wav"; subprocess.run(["ffmpeg","-y","-loglevel","error","-i",path,"-ac","1","-ar","16000",wav],check=True)
    y,sr=sf.read(wav,dtype="float32"); os.remove(wav)
    s=rec.create_stream(); s.accept_waveform(sr,y); rec.decode_stream(s); return s.result.text
def clean(t): return re.sub(r"[^一-鿿]","",t)
if __name__=="__main__":
    mp3,script=sys.argv[1],json.load(open(sys.argv[2],encoding="utf8"))
    ref=clean("".join(it.get("text","") for it in script["items"]))
    hyp=clean(asr(mp3))
    ratio=difflib.SequenceMatcher(None,ref,hyp).ratio()
    print(f"일치율 {ratio*100:.1f}%  (대본 {len(ref)}자 / 인식 {len(hyp)}자)")
    sm=difflib.SequenceMatcher(None,ref,hyp)
    for tag,i1,i2,j1,j2 in sm.get_opcodes():
        if tag!="equal" and (i2-i1>=2 or j2-j1>=2): print(f"  {tag}: 대본「{ref[i1:i2]}」 ↔ 인식「{hyp[j1:j2]}」")
    sys.exit(0 if ratio>=0.9 else 1)
