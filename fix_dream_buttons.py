#!/usr/bin/env python3
"""Safe, idempotent patch for the four daily quick buttons in Aunjai.
Run from repository root. Only touches index.html, backend-worker/index.js and sw.js.
Never deploys the independent Worker service.
"""
from pathlib import Path
from datetime import datetime
import shutil

root = Path.cwd()
paths = [root/'index.html',root/'backend-worker'/'index.js',root/'sw.js']
missing = [str(p) for p in paths if not p.is_file()]
if missing:
    raise SystemExit('Missing repository files: '+', '.join(missing))
f,b,sw = [p.read_text(encoding='utf-8') for p in paths]
if 'aunjai-dream-grounded-v4-' in f:
    print('Dream frontend fix already appears installed. No changes made.')
    raise SystemExit(0)

def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected one exact match; found {count}. No files saved.')
    return text.replace(old,new,1)

# Bust persistent quick-button response cache from previous releases.
f=replace_once(f, "aunjai-dream-grounded-v3-", "aunjai-dream-grounded-v4-", 'cache version')
# Keep cached results only briefly; always search again when the user explicitly taps a quick button.
f=replace_once(f,
 "if(saved&&Array.isArray(saved.sources)&&saved.sources.length)payload=saved",
 "if(saved&&Array.isArray(saved.sources)&&saved.sources.length&&Number(saved._cachedAt)>Date.now()-15*60*1000)payload=saved",
 'cache expiry')
f=replace_once(f,
 "localStorage.setItem(cacheKey,JSON.stringify(payload))",
 "localStorage.setItem(cacheKey,JSON.stringify({...payload,_cachedAt:Date.now()}))",
 'cache timestamp')
f=replace_once(f,
 "const intent=dreamQuick.dataset.dreamIntent,label=dreamQuick.dataset.dreamLabel||dreamQuick.textContent.trim();dreamState.record=null;",
 "const intent=dreamQuick.dataset.dreamIntent,label=dreamQuick.dataset.dreamLabel||dreamQuick.textContent.trim();try{localStorage.removeItem(dreamDailyCacheKey(intent))}catch{}dreamState.record=null;",
 'fresh click search')
# Handle slow or stuck network calls.
f=replace_once(f,
 "const response=await fetch(DREAM_CHAT_API,{method:'POST',mode:'cors',headers:{'Content-Type':'application/json'},body:JSON.stringify({message,history,intent})});",
 "const response=await fetch(DREAM_CHAT_API,{method:'POST',mode:'cors',signal:AbortSignal.timeout(60000),headers:{'Content-Type':'application/json'},body:JSON.stringify({message,history,intent})});",
 'request timeout')
f=replace_once(f,
 "dreamState.error=error?.message||'เชื่อมต่อข้อมูลไม่สำเร็จครับ';",
 "dreamState.error=(error?.name==='TimeoutError'||error?.name==='AbortError'?'การค้นหาใช้เวลานานเกิน 60 วินาที กรุณาลองกดค้นหาใหม่ครับ':error?.message)||'เชื่อมต่อข้อมูลไม่สำเร็จครับ';",
 'timeout error')
# Ignore late responses from chats already cleared.
f=replace_once(f,
 "async function sendDreamMessage(message,intent='dream'){const history=",
 "let dreamRequestId=0;\n  async function sendDreamMessage(message,intent='dream'){const requestId=++dreamRequestId;const history=",
 'request identifier')
f=replace_once(f,
 "dreamState.messages.push({role:'assistant',text:answer,sources:Array.isArray(payload.sources)?payload.sources:[]})",
 "if(requestId===dreamRequestId)dreamState.messages.push({role:'assistant',text:answer,sources:Array.isArray(payload.sources)?payload.sources:[]})",
 'late answer')
f=replace_once(f,
 "}catch(error){dreamState.error=",
 "}catch(error){if(requestId!==dreamRequestId)return;dreamState.error=",
 'late error')
f=replace_once(f,
 "}finally{dreamState.loading=false;go('luck-dream',false,false);const chatLog=",
 "}finally{if(requestId!==dreamRequestId)return;dreamState.loading=false;go('luck-dream',false,false);const chatLog=",
 'late render')
f=replace_once(f,
 "if(clearDream){dreamState={query:'',record:null,error:'',messages:[],loading:false};",
 "if(clearDream){dreamRequestId++;dreamState={query:'',record:null,error:'',messages:[],loading:false};",
 'new chat stale cancellation')
# Make independently checkable source links visible.
f=replace_once(f,
 'esc(shown)+(m.role===\'assistant\'?\'<div class="dream-ai-actions">',
 'esc(shown)+(m.role===\'assistant\'&&Array.isArray(m.sources)&&m.sources.length?\'<div class="dream-sources" style="margin-top:10px;font-size:12px;line-height:1.8"><strong>แหล่งอ้างอิง:</strong> \'+m.sources.slice(0,6).filter(s=>/^https?:\\/\\//i.test(String(s.url||\'\'))).map(s=>\'<a style="display:block;overflow-wrap:anywhere" href="\'+esc(s.url)+\'" target="_blank" rel="noopener noreferrer">\'+esc(s.title||\'เปิดแหล่งข้อมูล\')+\'</a>\').join(\'\')+\'</div>\':\'\')+(m.role===\'assistant\'?\'<div class="dream-ai-actions">',
 'visible sources')
# When backend explicitly reports no verifiable source, show the explanation, no invented numbers.
f=replace_once(f,
 "if(intent!=='dream'&&(!Array.isArray(payload.sources)||!payload.sources.length))throw new Error('วันนี้ยังไม่พบแหล่งข้อมูลที่อ้างอิงได้ จึงยังไม่แสดงตัวเลขครับ');",
 "if(intent!=='dream'&&(!Array.isArray(payload.sources)||!payload.sources.length)&&payload.verified!==false)throw new Error('วันนี้ยังไม่พบแหล่งข้อมูลที่อ้างอิงได้ จึงยังไม่แสดงตัวเลขครับ');",
 'verified fallback')

# More precise quick-button instructions: avoid hallucinating uploaded documents.
b=replace_once(b,
 'const prompt = common + "\\n\\nแนวทางคำตอบสำหรับหมวดนี้:\\n" + intentGuides[intent];',
 'const prompt = common + "\\n\\nแนวทางคำตอบสำหรับหมวดนี้:\\n" + intentGuides[intent] + (intent === "dream" ? "" : "\\nคำสั่งสำคัญ: นี่เป็นปุ่มค้นหาข้อมูลออนไลน์ ไม่ใช่การถามเกี่ยวกับเอกสารแนบหรือไฟล์ที่อัปโหลด ห้ามตอบว่าได้ตรวจเอกสารที่ได้รับหรือระบบไม่มีเอกสาร ให้ใช้ผลการค้นเว็บที่หาได้จริงเท่านั้น หากไม่พบแหล่งข้อมูลที่ตรวจสอบได้ ให้แจ้งอย่างตรงไปตรงมาและไม่แสดงเลขสมมติ");',
 'online-search prompt')
b=replace_once(b,
 'const contents = intent === "dream" && history.length ? history : [{ role: "user", parts: [{ text: message }] }];',
 'const contents = intent === "dream" && history.length ? history : [{ role: "user", parts: [{ text: intent === "dream" ? message : ("คำขอค้นเว็บจากปุ่ม: " + message + " โปรดค้นข้อมูลออนไลน์ภาษาไทยที่เกี่ยวข้องกับหมวด " + intent + " ตามคำสั่งระบบ แสดงชื่อแหล่งและลิงก์ที่ตรวจสอบได้ หากไม่มีแหล่งที่ระบุตัวเลขจริง อย่าแต่งตัวเลข") }] }];',
 'explicit search task')
b=replace_once(b,
 'if (!sources.length) return jsonResponse({ error: "การค้นครั้งนี้ไม่พบแหล่งเว็บอ้างอิงครับ ลองใหม่อีกครั้งภายหลัง" }, 502, cors);',
 'if (!sources.length && intent !== "dream") return jsonResponse({ answer: "ยังไม่พบแหล่งข้อมูลออนไลน์ที่ตรวจสอบได้ในหมวดนี้ครับ ลองค้นหาใหม่ภายหลังได้ โดยน้องอุ่นใจจะไม่สร้างตัวเลขขึ้นเอง", sources: [], searchQueries, intent, updatedAt: today, verified: false }, 200, cors);\n  if (!sources.length) return jsonResponse({ error: "การค้นครั้งนี้ไม่พบแหล่งเว็บอ้างอิงครับ ลองใหม่อีกครั้งภายหลัง" }, 502, cors);',
 'no-source fallback')
# Invalidate PWA shell cached by the service worker.
sw=replace_once(sw, "aunjai-current-pwa-v17", "aunjai-current-pwa-v18", 'service worker cache')

# Validate every change first, then create backups before writing.
stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
for path in paths:
    shutil.copy2(path,path.with_name(path.name+'.bak-'+stamp))
for path,contents in zip(paths,[f,b,sw]):
    path.write_text(contents,encoding='utf-8')
print('Patched index.html, backend-worker/index.js, sw.js; backups created.')
print('REMINDER: backend-worker/index.js must ALSO be deployed to the actual external Worker; GitHub Pages does not deploy it.')
