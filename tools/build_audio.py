"""HSK 숙제 음성 생성기.
usage:
  python3 build_audio.py script.json out.mp3 [--engine C|B]
script.json 형식:
  {"items":[ {"spk":"F","text":"第一题。","gap":0.8},
             {"spk":"M1","text":"..."}, {"spk":"F","text":"..."},
             {"pause":6}, ... ]}
  spk: F(여, 기본) / F2(여2) / M1 / M2(남)   gap: 발화 뒤 쉼(초, 기본 0.6)   pause: 무음(초)
engine C = ZipVoice(음성 복제, 자연스러움, 느림)  engine B = Matcha baker(여성 단일, 빠름; 남성은 C로 대체)
환경변수 MODELS_DIR (기본 ~/hsk-models). 먼저 setup.sh 실행.
"""
import sys, os, json, subprocess, time
import numpy as np, soundfile as sf, librosa, sherpa_onnx
HERE=os.path.dirname(os.path.abspath(__file__))
M=os.environ.get("MODELS_DIR",os.path.expanduser("~/hsk-models"))
SR=24000
PROMPTS=json.load(open(os.path.join(HERE,"prompts","prompts.json"),encoding="utf8"))
SPK2PROMPT={"F":"female1","F2":"female2","M1":"male1","M2":"male2"}

_zip=None; _mat=None
def zipvoice():
    global _zip
    if _zip is None:
        Z=f"{M}/sherpa-onnx-zipvoice-distill-int8-zh-en-emilia"
        _zip=sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
            zipvoice=sherpa_onnx.OfflineTtsZipvoiceModelConfig(tokens=f"{Z}/tokens.txt",encoder=f"{Z}/encoder.int8.onnx",decoder=f"{Z}/decoder.int8.onnx",
                vocoder=f"{M}/vocos_24khz.onnx",lexicon=f"{Z}/lexicon.txt,{M}/lexicon-en-us.txt"),num_threads=os.cpu_count() or 4),max_num_sentences=1))
    return _zip
def matcha(texts):
    global _mat
    if _mat is None:
        sys.path.insert(0,HERE); from zhlex import build_lexicon
        lex,_=build_lexicon(texts)
        B=f"{M}/matcha-icefall-zh-baker"
        _mat=sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
            matcha=sherpa_onnx.OfflineTtsMatchaModelConfig(acoustic_model=f"{B}/model-steps-3.onnx",vocoder=f"{M}/vocos-22khz-univ.onnx",
                lexicon=lex,tokens=f"{B}/tokens.txt",dict_dir=f"{B}/dict"),num_threads=os.cpu_count() or 4),
            rule_fsts=f"{B}/phone.fst,{B}/date.fst,{B}/number.fst",max_num_sentences=1))
    return _mat

def norm(y,sr):
    y=np.asarray(y,dtype=np.float32)
    if sr!=SR: y=librosa.resample(y,orig_sr=sr,target_sr=SR)
    yt,_=librosa.effects.trim(y,top_db=40)
    if len(yt)>SR*0.3: y=yt
    return y/(np.abs(y).max()+1e-6)*0.8

def synth_zip(spk,text,speed=1.0,steps=4):
    p=PROMPTS[SPK2PROMPT.get(spk,"female1")]
    y,sr=sf.read(os.path.join(HERE,"prompts",p["wav"]),dtype="float32")
    if y.ndim>1: y=y[:,0]
    c=sherpa_onnx.GenerationConfig(); c.reference_audio=y; c.reference_sample_rate=sr; c.reference_text=p["text"]; c.speed=speed; c.num_steps=steps
    a=zipvoice().generate(text,c); return norm(a.samples,a.sample_rate)
def synth_mat(spk,text,speed=1.0,texts=()):
    a=matcha(texts).generate(text,sid=0,speed=speed); return norm(a.samples,a.sample_rate)

def build(script,out,engine="C"):
    items=script["items"]; parts=[]
    ftexts=[it["text"] for it in items if "text" in it and it.get("spk","F").startswith("F")]
    t0=time.time()
    for it in items:
        if "pause" in it: parts.append(np.zeros(int(SR*it["pause"]),dtype=np.float32)); continue
        spk=it.get("spk","F"); text=it["text"]; speed=it.get("speed",1.0)
        if engine=="B" and spk.startswith("F"): y=synth_mat(spk,text,speed,ftexts)
        else: y=synth_zip(spk,text,speed)
        parts.append(y); parts.append(np.zeros(int(SR*it.get("gap",0.6)),dtype=np.float32))
    y=np.concatenate(parts); tmp=out+".wav"; sf.write(tmp,y,SR)
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",tmp,"-b:a","64k",out],check=True); os.remove(tmp)
    print(f"{out}: {len(y)/SR:.1f}s audio, built in {time.time()-t0:.0f}s")
    return out

if __name__=="__main__":
    args=sys.argv[1:]; eng="C"
    if "--engine" in args: i=args.index("--engine"); eng=args[i+1].upper(); del args[i:i+2]
    build(json.load(open(args[0],encoding="utf8")), args[1], eng)
