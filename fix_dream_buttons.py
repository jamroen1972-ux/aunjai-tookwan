#!/usr/bin/env python3
"""Patch local copies of aunjai-tookwan/index.html and backend-worker/index.js.
Run from the repository root. Backs up both originals; fails if expected code changed.
"""
from pathlib import Path
from datetime import datetime
import shutil

root = Path.cwd()
front = root / 'index.html'
back = root / 'backend-worker' / 'index.js'
for p in (front, back):
    if not p.is_file():
        raise SystemExit(f'Missing {p}; run from repository root')

def replace_once(s, old, new, label):
    count = s.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected one match, found {count}; no files modified')
    return s.replace(old, new, 1)

f = front.read_text(encoding='utf-8')
b = back.read_text(encoding='utf-8')

# Do not re-use cached daily results forever: cache expires after 20 minutes.
f = replace_once(f,
 "if(saved&&Array.isArray(saved.sources)&&saved.sources.length)payload=saved",
 "if(saved&&Array.isArray(saved.sources)&&saved.sources.length&&Number(saved._cachedAt)>Date.now()-20*60*1000)payload=saved",
 'frontend cache expiry')
f = replace_once(f,
 "localStorage.setItem(cacheKey,JSON.stringify(payload))",
 "localStorage.setItem(cacheKey,JSON.stringify({...payload,_cachedAt:Date.now()}))",
 'frontend cache timestamp')
# Make failed responses actionable and show source links in the chat.
f = replace_once(f,
 "dreamState.error=error?.message||'เชื่อมต่อข้อมูลไม่สำเร็จครับ';",
 "dreamState.error=(error?.name==='AbortError'?'การค้นหาใช้เวลานานเกินไป กรุณาลองใหม่ครับ':error?.message)||'เชื่อมต่อข้อมูลไม่สำเร็จครับ';",
 'frontend error')
f = replace_once(f,
 "const response=await fetch(DREAM_CHAT_API,{method:'POST',mode:'cors',headers:{'Content-Type':'application/json'},body:JSON.stringify({message,history,intent})});",
 "const response=await fetch(DREAM_CHAT_API,{method:'POST',mode:'cors',signal:AbortSignal.timeout(45000),headers:{'Content-Type':'application/json'},body:JSON.stringify({message,history,intent})});",
 'frontend request timeout')
f = replace_once(f,
 "dreamState.messages.push({role:'assistant',text:answer,sources:Array.isArray(payload.sources)?payload.sources:[]})",
 "if(requestId===dreamRequestId)dreamState.messages.push({role:'assistant',text:answer,sources:Array.isArray(payload.sources)?payload.sources:[]})",
 'frontend stale answer guard')
f = replace_once(f,
 "async function sendDreamMessage(message,intent='dream'){const history=",
 "let dreamRequestId=0;\n  async function sendDreamMessage(message,intent='dream'){const requestId=++dreamRequestId;const history=",
 'frontend request id')
f = replace_once(f,
 "}catch(error){dreamState.error=",
 "}catch(error){if(requestId!==dreamRequestId)return;dreamState.error=",
 'frontend stale error guard')
f = replace_once(f,
 "}finally{dreamState.loading=false;go('luck-dream',false,false);const chatLog=",
 "}finally{if(requestId!==dreamRequestId)return;dreamState.loading=false;go('luck-dream',false,false);const chatLog=",
 'frontend stale render guard')
f = replace_once(f,
 "if(clearDream){dreamState={query:'',record:null,error:'',messages:[],loading:false};",
 "if(clearDream){dreamRequestId++;dreamState={query:'',record:null,error:'',messages:[],loading:false};",
 'frontend clear guard')
# Render clickable source links from backend's already-provided source objects.
f = replace_once(f,
 "esc(shown)+(m.role==='assistant'?'<div class=\"dream-ai-actions\">",
 "esc(shown)+(m.role==='assistant'&&Array.isArray(m.sources)&&m.sources.length?'<div class=\"dream-sources\"><strong>แหล่งข้อมูล:</strong> '+m.sources.slice(0,6).filter(s=>/^https?:\\/\\//i.test(String(s.url||''))).map(s=>'<a href=\"'+esc(s.url)+'\" target=\"_blank\" rel=\"noopener noreferrer\">'+esc(s.title||'เปิดแหล่งข้อมูล')+'</a>').join(' · ')+'</div>':'')+(m.role==='assistant'?'<div class=\"dream-ai-actions\">",
 'frontend source links')
# Add an explicit refresh button for the four intent types.
f = replace_once(f,
 "const intent=dreamQuick.dataset.dreamIntent,label=dreamQuick.dataset.dreamLabel||dreamQuick.textContent.trim();dreamState.record=null;",
 "const intent=dreamQuick.dataset.dreamIntent,label=dreamQuick.dataset.dreamLabel||dreamQuick.textContent.trim();try{localStorage.removeItem(dreamDailyCacheKey(intent))}catch{}dreamState.record=null;",
 'frontend refresh on tap')

# Backend: retain valid textual answers even if grounding metadata is missing.
# This does NOT permit invented numbers: the prompt still prohibits them.
b = replace_once(b,
 'if (!sources.length) return jsonResponse({ error: "การค้นครั้งนี้ไม่พบแหล่งเว็บอ้างอิงครับ ลองใหม่อีกครั้งภายหลัง" }, 502, cors);',
 'if (!sources.length && intent !== "dream") return jsonResponse({ answer: "ยังไม่พบแหล่งข้อมูลที่ตรวจสอบได้สำหรับหมวดนี้ กรุณาลองค้นหาใหม่ภายหลังครับ", sources: [], searchQueries, intent, updatedAt: today, verified: false }, 200, cors);\n  if (!sources.length) return jsonResponse({ error: "การค้นครั้งนี้ไม่พบแหล่งเว็บอ้างอิงครับ ลองใหม่อีกครั้งภายหลัง" }, 502, cors);',
 'backend no-sources graceful response')
# Frontend accepts an explicit verified:false response as an informational result.
f = replace_once(f,
 "if(intent!=='dream'&&(!Array.isArray(payload.sources)||!payload.sources.length))throw new Error('วันนี้ยังไม่พบแหล่งข้อมูลที่อ้างอิงได้ จึงยังไม่แสดงตัวเลขครับ');",
 "if(intent!=='dream'&&(!Array.isArray(payload.sources)||!payload.sources.length)&&payload.verified!==false)throw new Error('วันนี้ยังไม่พบแหล่งข้อมูลที่อ้างอิงได้ จึงยังไม่แสดงตัวเลขครับ');",
 'frontend unverified informative response')

stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
for p in (front, back):
    shutil.copy2(p, p.with_name(p.name + '.bak-' + stamp))
front.write_text(f, encoding='utf-8')
back.write_text(b, encoding='utf-8')
print('Updated index.html and backend-worker/index.js; originals backed up.')
