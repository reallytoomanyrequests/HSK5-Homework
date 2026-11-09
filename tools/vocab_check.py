"""HSK 3.0 어휘 범위 검사기.
usage: python3 vocab_check.py "중국어 텍스트" [--max 5]
      또는 python3 vocab_check.py --file set.json   (모든 중국어 문자열 검사)
출력: 레벨별 단어 비율, 5급 초과(6급/범위 밖) 단어 목록.
"""
import sys, json, re, os, logging
import jieba; jieba.setLogLevel(logging.ERROR)
HERE=os.path.dirname(os.path.abspath(__file__))
LISTS=json.load(open(os.path.join(HERE,"..","spec","hsk30_lists.json"),encoding="utf8"))
WORDS=LISTS["words"]; HANZI=LISTS["hanzi"]
for w in WORDS: jieba.add_word(w, freq=2000)   # HSK 단어 우선 분절
# 고유명사·기능어 등 검사 제외 (인명, 지명, 숫자, 문장부호)
SKIP=set("的了着过吗呢吧啊呀嘛哦嗯啦哎唉".split()) | {"小王","小张","小李","小刘","小陈","李华","王明","张华","北京","上海","西安","中国","汉语"}
def level_of(w):
    if w in WORDS: return WORDS[w]
    # 단어가 없으면 글자 단위로 최고 레벨 (모든 글자가 5급 이내면 '조합어'로 허용)
    if all(c in HANZI for c in w): return max(HANZI[c] for c in w)+0.5   # .5 = 글자 조합
    return 9
def check(text, max_level=5):
    toks=[t for t in jieba.lcut(text) if re.fullmatch(r"[一-鿿]+",t)]
    toks=[t for t in toks if t not in SKIP and not re.fullmatch(r"[一二三四五六七八九十百千万零两]+",t)]
    res={"total":len(toks),"over":[],"combo":[],"by_level":{}}
    for t in toks:
        lv=level_of(t)
        key=str(int(lv)) if lv<9 else "X"
        res["by_level"][key]=res["by_level"].get(key,0)+1
        if lv==9 or int(lv)>max_level: res["over"].append((t,key))
        elif lv!=int(lv): res["combo"].append((t,key))
    res["over"]=sorted(set(res["over"])); res["combo"]=sorted(set(res["combo"]))
    res["over_ratio"]=round(len([1 for t in toks if level_of(t)==9 or int(level_of(t))>max_level])/max(len(toks),1)*100,1)
    return res
def strings_from(obj):
    if isinstance(obj,str):
        if re.search(r"[一-鿿]",obj): yield obj
    elif isinstance(obj,dict):
        for v in obj.values(): yield from strings_from(v)
    elif isinstance(obj,list):
        for v in obj: yield from strings_from(v)
if __name__=="__main__":
    args=sys.argv[1:]; mx=5
    if "--max" in args: i=args.index("--max"); mx=int(args[i+1]); del args[i:i+2]
    if args and args[0]=="--file":
        text="\n".join(strings_from(json.load(open(args[1],encoding="utf8"))))
    else: text=" ".join(args)
    r=check(text,mx)
    print(f"단어 {r['total']}개 | 레벨 분포 {dict(sorted(r['by_level'].items()))} | 5급 초과 비율 {r['over_ratio']}%")
    if r["over"]: print("5급 초과/범위 밖:", " ".join(f"{w}({l})" for w,l in r["over"]))
    if r["combo"]: print("글자 조합어(사전에 없음, 글자는 범위 내):", " ".join(w for w,_ in r["combo"]))
