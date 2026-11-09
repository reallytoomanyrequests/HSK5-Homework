"""Matcha(엔진B)용 발음 보정: 사전에 없는 단어를 pypinyin + 성조변화 규칙으로 추가한 임시 사전 생성"""
import re, jieba, logging
jieba.setLogLevel(logging.ERROR)
from pypinyin import lazy_pinyin, Style
import os
B=os.path.join(os.environ.get("MODELS_DIR",os.path.expanduser("~/hsk-models")),"matcha-icefall-zh-baker")
LEX={}
for line in open(f"{B}/lexicon.txt",encoding="utf8"):
    p=line.rstrip("\n").split(" ",1)
    if len(p)==2: LEX[p[0]]=p[1]
TOK=set(l.split()[0] for l in open(f"{B}/tokens.txt",encoding="utf8") if l.strip())
def sandhi(syls):
    s=[list(re.match(r"([a-z]+)(\d?)",x).groups()) for x in syls]
    n=len(s)
    for i in range(n-1):           # 一 / 不
        nxt=s[i+1][1]
        if s[i][0]=="yi" and nxt:
            s[i][1]="2" if nxt=="4" else ("4" if nxt in "123" else s[i][1])
        if s[i][0]=="bu" and nxt=="4": s[i][1]="2"
    for i in range(n-2,-1,-1):     # 3-3
        if s[i][1]=="3" and s[i+1][1]=="3": s[i][1]="2"
    out=[]
    for base,t in s:
        if t=="5":
            out.append(base if base in TOK else base+"5")
        else: out.append(base+t)
    return out
def word_pinyin(w):
    full=lazy_pinyin(w,style=Style.TONE3,neutral_tone_with_five=True)
    syl=sandhi(full)
    fixed=[]
    for x,orig in zip(syl,lazy_pinyin(w,style=Style.TONE3)):
        if x in TOK: fixed.append(x)
        elif orig in TOK: fixed.append(orig)
        else: return None
    return " ".join(fixed)
def build_lexicon(texts, out="/tmp/_lex_B.txt", verbose=False):
    add={}
    for t in texts:
        for w in jieba.lcut(t):
            if not re.search(r"[一-鿿]",w) or w in LEX or w in add or len(w)<2: continue
            py=word_pinyin(w)
            if py: add[w]=py
    with open(out,"w",encoding="utf8") as f:
        f.write(open(f"{B}/lexicon.txt",encoding="utf8").read())
        for w,py in add.items(): f.write(f"{w} {py}\n")
    if verbose:
        for w,py in add.items(): print(w,py)
    return out, add
if __name__=="__main__":
    import sys; build_lexicon([sys.argv[1]],verbose=True)
