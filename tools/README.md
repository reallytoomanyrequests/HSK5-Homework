# tools — 매일 숙제 생성 파이프라인

```
bash tools/setup.sh                      # 모델 준비 (처음 1회, ~10분)
python3 tools/vocab_check.py --file homework/DATE/set.json      # 어휘 범위 검사 (5급 초과 3% 이하)
python3 tools/build_audio.py homework/DATE/listening.script.json homework/DATE/listening1.mp3   # 음성
python3 tools/asr_check.py homework/DATE/listening1.mp3 homework/DATE/listening.script.json     # 자가검수 (90%↑)
```

## set.json (학생용) 스키마
```json
{"date":"YYYY-MM-DD","title":"Day N","note":"한 줄 안내",
 "sections":[
  {"type":"listening","part":1,"title":"듣기 제1부분","audio":"listening1.mp3","instruction":"...",
   "questions":[{"n":1,"q":"男的最可能在哪儿？","options":["A","B","C","D"]}]},
  {"type":"listening","part":2,"title":"듣기 제2부분","audio":"listening2.mp3","questions":[...]},
  {"type":"reading","part":1,"title":"독해 제1부분","passage":"빈칸 있는 지문(빈칸은 ＿＿①＿＿ 형식)","questions":[{"n":1,"q":"①","options":[...]}]},
  {"type":"reading","part":2,"title":"독해 제2부분","passage":"선택지 문장 A~E 포함","questions":[{"n":1,"q":"문장 순서 ①에 들어갈 것","options":[...]}]},
  {"type":"reading","part":3,"title":"독해 제3부분","passage":"지문","questions":[...]},
  {"type":"writing","part":2,"title":"쓰기 제2부분","prompt":"题目 원문","minChars":200,"timeSec":1500},
  {"type":"writing","part":1,"title":"쓰기 제1부분","images":["w1_1.png","w1_2.png","w1_3.png","w1_4.png"],"minChars":100,"timeSec":900},
  {"type":"speaking","part":1,"title":"말하기 제1부분","audio":"speaking1.mp3","prepSec":0,"answerSec":90},
  {"type":"speaking","part":2,"title":"말하기 제2부분","images":["s2_1.png","s2_2.png","s2_3.png"],"prepSec":180,"answerSec":120},
  {"type":"speaking","part":3,"title":"말하기 제3부분","prompt":"问题 원문","prepSec":210,"answerSec":150}
 ]}
```
- 듣기·독해 문항 번호 `n`은 같은 type 안에서 회차 내 유일해야 함 (자동 채점 키).

## answers.json (정답·해설) 스키마
```json
{"date":"YYYY-MM-DD",
 "listening":[{"n":1,"answer":"A","script":"대본 전문","explain":"한국어 해설"}],
 "reading":[{"n":1,"answer":"B","explain":"..."}],
 "writing":{"model":"모범답안","points":["체크리스트 1","..."]},
 "speaking":[{"part":1,"script":"지문","model":"모범답변","points":["..."]}]}
```

## 음성 대본 script.json
`{"items":[{"spk":"F","text":"第一题。","gap":0.8},{"spk":"M1","text":"..."},{"spk":"F","text":"..."},{"pause":0.6},{"spk":"F","text":"问：…？"},{"pause":10}]}`
- 화자: F(여1, 기본 내레이션·질문) F2(여2) M1·M2(남). 대화마다 남자 화자를 M1/M2 번갈아.
- 실전 간격: 질문 뒤 답 고르는 시간 10초(1부), 2부 단문은 질문 3개 각 10초.
