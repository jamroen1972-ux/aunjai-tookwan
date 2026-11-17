แก้ AI ทำนายฝัน (แชท + ปุ่มลัด 4 ปุ่ม) — ไฟล์ที่เปลี่ยน
- backend-worker/index.js  (ต้อง Deploy ไปที่ Worker จริงด้วย GitHub Pages ไม่ได้ deploy ให้)
- index.html
- sw.js (cache v19)
ลบแล้ว: fix_dream_buttons.py และ .github/workflows/apply-dream-fix.yml (แพตช์เก่าใช้กับรุ่นนี้ไม่ได้อีก)

ขั้นตอน
1. อัปโหลด index.html และ sw.js ไปที่ root ของ repo aunjai-tookwan (อย่าอัปไป English Adventure)
2. นำ backend-worker/index.js ไป Deploy ทับ Worker ที่ให้บริการ API จริง
3. ใน Worker ตั้งค่า GEMINI_GROUNDING_MODEL = gemini-3.8-flash (หรือไม่ตั้งก็ได้ ค่าเริ่มต้นใหม่คือรุ่นนี้)
4. ตรวจว่ามี Secret GEMINI_API_KEY อยู่
5. เปิดเว็บแล้วรีเฟรช 1-2 ครั้งให้ Service Worker รุ่นใหม่ทำงาน
