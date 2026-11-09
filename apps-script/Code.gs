/**
 * 기솔의 HSK 5급 스터디룸 — 서버 스크립트 (Google Apps Script)
 * 구글 시트 > 확장 프로그램 > Apps Script 에 붙여넣고 "웹 앱"으로 배포하세요.
 *   배포 설정: 실행 사용자 = 나 / 액세스 권한 = 모든 사용자
 *   코드를 고친 뒤에는 "배포 관리 > 새 버전"으로 다시 배포해야 반영됩니다.
 */

// ===================== 여기만 채우면 됩니다 =====================
const TEACHER_PIN   = "1234";          // 선생님 모드 비밀번호 (앱에서 입력)
const APP_URL       = "https://reallytoomanyrequests.github.io/HSK5-Homework/";   // GitHub Pages 주소 (끝에 / 포함)
const STUDENT_EMAIL = "";              // 기솔 이메일: 피드백 알림 (비우면 안 보냄)
const TEACHER_EMAIL = "";              // 네 이메일: 제출 알림 (비우면 안 보냄)
const NTFY_STUDENT  = "";              // ntfy 토픽 (예: gisol-hsk5-7f3k) : 기솔 폰 푸시 알림. 비우면 안 보냄
const NTFY_TEACHER  = "";              // ntfy 토픽 : 네 폰 푸시 알림 (제출 시)
// ===============================================================

const SH_SUB = "제출", SH_FB = "피드백", SH_LOG = "듣기기록", FOLDER_NAME = "HSK5 숙제 녹음";
const PAGES_BASE = APP_URL + "homework/";
const SUB_HEADERS = ["제출 시각", "숙제 날짜", "학생", "듣기·독해 답", "재생 횟수", "자동 채점", "오답 문항", "쓰기 글자수", "쓰기 전문", "말하기", "녹음 파일", "요약", "쓰기 소요시간"];
const FB_HEADERS  = ["작성 시각", "숙제 날짜", "영역", "코멘트"];
const LOG_HEADERS = ["시각", "학생", "출처", "문제 위치", "연습 방식", "결과", "메모"];

// ---------- 라우팅 ----------
function doGet(e) {
  const p = (e && e.parameter) || {};
  try {
    if (p.action === "all")    return out({ ok: true, days: statusAll() });
    if (p.action === "status") return out({ ok: true, ...statusDay(p.day, p.pin === TEACHER_PIN) });
    if (p.action === "pin")    return out({ ok: p.pin === TEACHER_PIN });
    if (p.action === "logs")   return out({ ok: true, logs: listLogs() });
    return out({ ok: true, message: "HSK5 스터디룸 서버 동작 중" });
  } catch (err) { return out({ ok: false, error: String(err) }); }
}

function doPost(e) {
  try {
    const d = JSON.parse(e.postData.contents);
    if (d.action === "feedback") return out(saveFeedback(d));
    if (d.action === "log")      return out(saveLog(d));
    return out(saveSubmission(d));
  } catch (err) { return out({ ok: false, error: String(err) }); }
}

// ---------- 제출 저장 ----------
function saveSubmission(d) {
  const sh = getSheet(SH_SUB, SUB_HEADERS);
  const links = [];
  (d.recordings || []).forEach(function (r) {
    const root = getOrCreateFolder(DriveApp.getRootFolder(), FOLDER_NAME);
    const dayF = getOrCreateFolder(root, d.day);
    const blob = Utilities.newBlob(Utilities.base64Decode(r.data), r.mime || "audio/webm", r.name);
    const f = dayF.createFile(blob);
    f.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
    links.push(r.name + "|" + f.getUrl());
  });

  const key = fetchAnswers(d.day);
  let answerText = [], plays = [], right = 0, total = 0, wrong = [];
  (d.sections || []).forEach(function (s) {
    if (s.type !== "listening" && s.type !== "reading") return;
    const list = key ? ((s.type === "listening" ? key.listening : key.reading) || []) : [];
    const parts = [];
    Object.keys(s.answers).sort(function (a, b) { return a - b; }).forEach(function (n) {
      const mine = s.answers[n] || "-";
      const a = list.filter(function (x) { return String(x.n) === String(n); })[0];
      let mark = "";
      if (a) { total++; if (a.answer === mine) right++; else { wrong.push(s.title + " " + n + "번(정답 " + a.answer + ")"); mark = "✗"; } }
      parts.push(n + "." + mine + mark);
    });
    answerText.push("[" + s.title + "] " + parts.join(" "));
    if (s.plays) plays.push(s.title + " " + s.plays + "회");
  });
  const speaking = (d.sections || []).filter(function (s) { return s.type === "speaking"; })
    .map(function (s) { return s.title + ": " + (s.recorded ? "녹음 " + s.dur + (s.attached ? "" : " (파일 없음)") : "녹음 없음"); }).join("\n");
  const score = total ? right + "/" + total : "";

  sh.appendRow([new Date(), d.day, d.student || "", answerText.join("\n"), plays.join(", "), score, wrong.join("\n"),
                d.writingCount || 0, d.writing || "", speaking, links.join("\n"), d.summary || "", d.writingTime || ""]);

  notify("teacher", "📥 " + (d.student || "학생") + " 숙제 제출 (" + d.day + ")",
         (score ? "듣기·독해 " + score + " · " : "") + "쓰기 " + (d.writingCount || 0) + "자 · 녹음 " + (d.recordings || []).length + "개", d.day);
  return { ok: true, score: score };
}

// ---------- 피드백 저장 ----------
function saveFeedback(d) {
  if (d.pin !== TEACHER_PIN) return { ok: false, error: "비밀번호가 틀렸어요" };
  const sh = getSheet(SH_FB, FB_HEADERS);
  sh.appendRow([new Date(), d.day, d.cat || "", d.text || ""]);
  notify("student", "💬 선생님 피드백 도착 (" + d.day + ")", (d.text || "").slice(0, 140), d.day);
  return { ok: true };
}

// ---------- 듣기 연습기록 ----------
function saveLog(d) {
  const sh = getSheet(SH_LOG, LOG_HEADERS);
  sh.appendRow([new Date(), d.student || "", d.src || "", d.where || "", d.how || "", d.result || "", d.memo || ""]);
  return { ok: true };
}
function listLogs() {
  return rows(SH_LOG, LOG_HEADERS).map(function (r) { return { time: r[0], student: r[1], src: r[2], where: r[3], how: r[4], result: r[5], memo: r[6] }; });
}

// ---------- 조회 ----------
function rows(name, headers) {
  const sh = getSheet(name, headers);
  const v = sh.getDataRange().getValues();
  return v.slice(1).filter(function (r) { return r[0]; });
}
function statusAll() {
  const out = {};
  rows(SH_SUB, SUB_HEADERS).forEach(function (r) {
    const day = fmtDay(r[1]); const o = out[day] = out[day] || { submitted: 0, score: "", feedback: 0 };
    o.submitted++; o.score = r[5] || o.score; o.lastSubmit = r[0];
  });
  rows(SH_FB, FB_HEADERS).forEach(function (r) {
    const day = fmtDay(r[1]); const o = out[day] = out[day] || { submitted: 0, score: "", feedback: 0 };
    o.feedback++; o.lastFeedback = r[0];
  });
  return out;
}
function statusDay(day, isTeacher) {
  const subs = rows(SH_SUB, SUB_HEADERS).filter(function (r) { return fmtDay(r[1]) === day; }).map(function (r) {
    const base = { time: r[0], student: r[2], answers: r[3], plays: r[4], score: r[5], wrong: r[6], writingCount: r[7], speaking: r[9], writingTime: r[12] || "" };
    if (isTeacher) { base.writing = r[8]; base.recordings = String(r[10] || "").split("\n").filter(Boolean).map(function (x) { const p = x.split("|"); return { name: p[0], url: p[1] }; }); }
    return base;
  });
  const fb = rows(SH_FB, FB_HEADERS).filter(function (r) { return fmtDay(r[1]) === day; }).map(function (r) { return { time: r[0], cat: r[2], text: r[3] }; });
  return { submissions: subs, feedback: fb, teacher: !!isTeacher };
}
function fmtDay(v) {
  if (v instanceof Date) return Utilities.formatDate(v, Session.getScriptTimeZone(), "yyyy-MM-dd");
  return String(v).slice(0, 10);
}

// ---------- 알림 ----------
function notify(who, title, body, day) {
  const email = who === "student" ? STUDENT_EMAIL : TEACHER_EMAIL;
  const topic = who === "student" ? NTFY_STUDENT : NTFY_TEACHER;
  const link = APP_URL + "#" + day;
  try { if (email) MailApp.sendEmail({ to: email, subject: title, body: body + "\n\n" + link }); } catch (e) {}
  try {
    if (topic) UrlFetchApp.fetch("https://ntfy.sh", { method: "post", contentType: "application/json",
      payload: JSON.stringify({ topic: topic, title: title, message: body, click: link, tags: [who === "student" ? "speech_balloon" : "inbox_tray"] }), muteHttpExceptions: true });
  } catch (e) {}
}

// ---------- 유틸 ----------
function getSheet(name, headers) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(name);
  if (!sh) { sh = ss.insertSheet(name); sh.appendRow(headers); sh.setFrozenRows(1); sh.getRange(1, 1, 1, headers.length).setFontWeight("bold"); }
  return sh;
}
function fetchAnswers(day) {
  try { const res = UrlFetchApp.fetch(PAGES_BASE + day + "/answers.json", { muteHttpExceptions: true }); if (res.getResponseCode() === 200) return JSON.parse(res.getContentText()); } catch (e) {}
  return null;
}
function getOrCreateFolder(parent, name) { const it = parent.getFoldersByName(name); return it.hasNext() ? it.next() : parent.createFolder(name); }
function out(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }
