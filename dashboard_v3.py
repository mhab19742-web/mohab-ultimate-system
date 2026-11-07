
import os
import json
import base64
import requests
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer

CONFIG_DIR = Path.home() / ".config" / "mohab-ai"
KEY_FILE = CONFIG_DIR / ".env"
MEMORY_FILE = CONFIG_DIR / "history.json"

TEXT_MODEL = "openai/gpt-oss-20b"
VISION_MODEL = "qwen/qwen3.8-27b"
MAX_MESSAGES = 20
MAX_IMAGE_BYTES = 8 * 1024 * 1024

SYSTEM_PROMPT = """
أنت MOHAB AI، مساعد ذكي من صنع مهاب الكينج.
تحدث باللغة المصرية البسيطة.
كن ودودًا ومحترمًا ومفيدًا.
افهم سياق المحادثة السابقة.
عند تحليل الصور، صف ما يظهر بوضوح ولا تخمن التفاصيل.
"""

def load_key():
    if not KEY_FILE.exists():
        return None
    for line in KEY_FILE.read_text().splitlines():
        if line.startswith("GROQ_API_KEY="):
            return line.split("=", 1)[1].strip()
    return None

def load_memory():
    try:
        data = json.loads(MEMORY_FILE.read_text())
        if isinstance(data, list):
            return [
                x for x in data
                if isinstance(x, dict)
                and x.get("role") in ("user", "assistant")
                and isinstance(x.get("content"), str)
            ][-MAX_MESSAGES:]
    except (OSError, json.JSONDecodeError):
        pass
    return []

def save_memory(history):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    MEMORY_FILE.write_text(
        json.dumps(history[-MAX_MESSAGES:], ensure_ascii=False, indent=2)
    )
    os.chmod(MEMORY_FILE, 0o600)

def send_request(messages, api_key, model):
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "messages": messages,
            "max_completion_tokens": 1024
        },
        timeout=90
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

def detect_image_type(data):
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    return None

HTML = r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#080808">
<link rel="manifest" href="/manifest.json">
<link rel="icon" type="image/png" href="/icon-192.png">

<title>MOHAB EL KING</title>
<style>
*{box-sizing:border-box}
body{
 margin:0;min-height:100vh;padding:20px;
 background:radial-gradient(ellipse at top,#29200b,#101010 40%,#020202);
 color:#f5bd42;font-family:Arial,sans-serif;text-align:center;
}
header{
 padding:25px 10px;border:1px solid #a77b22;border-radius:18px;
 background:linear-gradient(135deg,#17120a,#050505);
 box-shadow:0 0 25px #a77b2244;
}
h1{color:#ffd36a;text-shadow:0 0 15px #d99b27;margin:5px}
.subtitle{color:#aaa;font-size:13px}
nav{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:22px 0}
button{
 padding:15px 8px;border:1px solid #c49332;border-radius:14px;
 color:#ffda83;font-size:15px;font-weight:bold;
 background:linear-gradient(145deg,#33230a,#100d08);
 box-shadow:0 0 13px #b7832944,inset 0 0 12px #d69d2922;
 cursor:pointer;
}
button:active{transform:scale(.96);box-shadow:0 0 25px #ffc34d}
button:disabled{opacity:.5}
.page{
 display:none;padding:20px 12px;border:1px solid #8e6826;
 border-radius:16px;background:linear-gradient(145deg,#15120d,#050505);
 box-shadow:0 0 20px #a77b2233;min-height:230px;
}
.page.active{display:block}
h2{color:#ffd36a}
.output{
 margin:15px auto;padding:14px;min-height:100px;max-height:280px;
 overflow-y:auto;white-space:pre-wrap;overflow-wrap:anywhere;
 background:#020702;border:1px solid #146c35;border-radius:12px;
 color:#00ff66;text-align:left;direction:ltr;
 font-family:monospace;line-height:1.6;
}
.king-effect{text-align:center;padding-top:25px;line-height:2.5;animation:appear 1.5s;direction:rtl}
.king-success{color:#00ff66;font-size:20px;text-shadow:0 0 12px #00ff66}
.king-field{color:#00ff99;font-size:23px;font-weight:bold;text-shadow:0 0 10px #00ff99;animation:glow 1s infinite alternate}
.king-name{color:#f5bd42;font-size:23px;font-weight:bold;text-shadow:0 0 12px #f5bd42;animation:gold 1.5s infinite alternate}
@keyframes glow{from{text-shadow:0 0 5px #00ff99}to{text-shadow:0 0 25px #00ff99}}
@keyframes gold{from{text-shadow:0 0 5px #f5bd42}to{text-shadow:0 0 25px #f5bd42}}
@keyframes appear{from{opacity:0;transform:scale(.7)}to{opacity:1;transform:scale(1)}}
.info{background:#090909;padding:15px;border-radius:12px;border:1px solid #75551d;line-height:2}
input{
 width:100%;padding:13px;border-radius:10px;border:1px solid #b88a32;
 background:#090909;color:white;margin:10px 0;font-size:16px;
}
#chat{
 text-align:right;direction:rtl;min-height:100px;max-height:350px;
 overflow-y:auto;line-height:1.8;overflow-wrap:anywhere;
}
.chat-message{
 padding:10px;margin:9px 0;border-radius:10px;
 background:#17130b;border:1px solid #70521e;color:#fff;
 text-align:right;white-space:pre-wrap;
}
.chat-message.ai{border-color:#08783a;background:#06140b}
#imagePreview{max-width:100%;max-height:220px;border-radius:12px;margin:8px auto;display:none}
.hint{color:#aaa;font-size:12px;line-height:1.8}
</style>
</head>
<body>

<header>
<h1>👑 MOHAB EL KING 👑</h1>
<div class="subtitle">ULTIMATE MATRIX SYSTEM V3.2</div>
</header>

<nav>
<button onclick="showPage('home')">🏠 الرئيسية</button>
<button onclick="showPage('matrix')">⚡ MATRIX KING</button>
<button onclick="showPage('system')">📱 SYSTEM CONTROL</button>
<button onclick="showPage('cyber')">🌐 CYBER KING</button>
<button onclick="showPage('ai')">🤖 MOHAB AI</button>
</nav>

<section id="home" class="page active">
<h2>أهلاً بك في النظام الملكي</h2>
<div class="info">
👑 MOHAB EL KING 👑<br>
⚡ راكب المجال ⚡<br>
النظام جاهز للتشغيل
</div>
</section>

<section id="matrix" class="page">
<h2>⚡ MATRIX KING ⚡</h2>
<div id="matrixRain" class="output">MOHAB EL KING 👑</div>
<button onclick="startMatrix()">▶ تشغيل MATRIX</button>
</section>

<section id="system" class="page">
<h2>📱 SYSTEM CONTROL</h2>
<div id="device" class="info">اضغط لعرض معلومات المتصفح والجهاز المتاحة</div>
<button onclick="getDevice()">عرض المعلومات</button>
</section>

<section id="cyber" class="page">
<h2>🌐 CYBER KING</h2>
<div id="network" class="info">اضغط لفحص حالة اتصال الإنترنت</div>
<button onclick="checkNetwork()">فحص الاتصال</button>
</section>

<section id="ai" class="page">
<h2>🤖 MOHAB AI</h2>
<div id="chat" class="info">أهلاً بك! ابعتلي رسالة أو صورة وأنا هساعدك 👑</div>

<img id="imagePreview" alt="معاينة الصورة">

<input id="message" placeholder="اكتب رسالتك أو اسأل عن الصورة">

<input id="imageInput" type="file" accept="image/jpeg,image/png,image/webp">

<div class="hint">يدعم JPG و PNG و WEBP، بحد أقصى 8 ميجابايت.</div>

<button id="sendButton" onclick="sendMessage()">إرسال إلى MOHAB AI</button>
</section>

<script>
function showPage(id){
 document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
 document.getElementById(id).classList.add('active');
}

function getDevice(){
 document.getElementById('device').innerHTML=
 'المتصفح: '+navigator.userAgent+
 '<br>حالة الاتصال: '+(navigator.onLine?'متصل':'غير متصل')+
 '<br>حجم الشاشة: '+screen.width+' × '+screen.height;
}

function checkNetwork(){
 document.getElementById('network').textContent=
 navigator.onLine?'🟢 الاتصال متاح':'🔴 لا يوجد اتصال';
}

function startMatrix(){
 let box=document.getElementById('matrixRain');
 box.innerHTML='';
 let chars='01MOHABKING#$%&@';
 let count=0;
 let timer=setInterval(()=>{
   let line='';
   for(let i=0;i<40;i++) line+=chars[Math.floor(Math.random()*chars.length)];
   box.textContent+=line+'\n';
   box.scrollTop=box.scrollHeight;
   count++;
   if(count>=35){
     clearInterval(timer);
     box.innerHTML=`
       <div class="king-effect">
         <div class="king-success">تمت السيطرة بنجاح ✓</div>
         <div class="king-field">⚡ راكب المجال ⚡</div>
         <div class="king-name">👑 MOHAB EL KING 👑</div>
       </div>`;
     box.scrollTop=0;
   }
 },150);
}

const imageInput=document.getElementById('imageInput');
const preview=document.getElementById('imagePreview');

imageInput.addEventListener('change',()=>{
 const file=imageInput.files[0];
 if(!file){preview.style.display='none';return;}
 if(file.size>8*1024*1024){
   alert('الصورة أكبر من 8 ميجابايت');
   imageInput.value='';
   preview.style.display='none';
   return;
 }
 preview.src=URL.createObjectURL(file);
 preview.style.display='block';
});

function addChat(text,isAI){
 const div=document.createElement('div');
 div.className='chat-message'+(isAI?' ai':'');
 div.textContent=(isAI?'🤖 MOHAB AI: ':'👤 أنت: ')+text;
 document.getElementById('chat').appendChild(div);
 document.getElementById('chat').scrollTop=999999;
}

async function sendMessage(){
 const input=document.getElementById('message');
 const file=imageInput.files[0];
 const question=input.value.trim();
 const button=document.getElementById('sendButton');

 if(!question && !file)return;

 if(file && file.size>8*1024*1024){
   alert('الصورة أكبر من 8 ميجابايت');
   return;
 }

 button.disabled=true;
 button.textContent='جاري الإرسال...';

 if(question)addChat(question,false);
 if(file)addChat('📷 تم اختيار صورة: '+file.name,false);

 try{
   let imageData=null;
   if(file){
     imageData=await new Promise((resolve,reject)=>{
       const reader=new FileReader();
       reader.onload=()=>resolve(reader.result);
       reader.onerror=reject;
       reader.readAsDataURL(file);
     });
   }

   const response=await fetch('/api/chat',{
     method:'POST',
     headers:{'Content-Type':'application/json'},
     body:JSON.stringify({question:question,image:imageData})
   });

   const data=await response.json();
   if(!response.ok)throw new Error(data.error||'حدث خطأ في الاتصال');

   addChat(data.answer,true);
   input.value='';
   imageInput.value='';
   preview.style.display='none';

 }catch(error){
   addChat('حصلت مشكلة: '+error.message,true);
 }finally{
   button.disabled=false;
   button.textContent='إرسال إلى MOHAB AI';
 }
}
</script>
</body>
</html>
"""

class Handler(BaseHTTPRequestHandler):

    def send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        files = {
            "/manifest.json": ("manifest.json", "application/manifest+json"),
            "/icon-192.png": ("icon-192.png", "image/png"),
            "/icon-512.png": ("icon-512.png", "image/png"),
        }

        if self.path in files:
            filename, content_type = files[self.path]
            body = Path(filename).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path != "/":
            self.send_error(404)
            return

        body = HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/api/chat":
            self.send_json(404, {"error": "المسار غير موجود"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 12 * 1024 * 1024:
                self.send_json(413, {"error": "حجم الطلب غير مناسب"})
                return

            raw = self.rfile.read(length)
            data = json.loads(raw.decode("utf-8"))

            question = str(data.get("question", "")).strip()
            image = data.get("image")

            if not question and not image:
                self.send_json(400, {"error": "اكتب رسالة أو اختر صورة"})
                return

            api_key = load_key()
            if not api_key:
                self.send_json(500, {"error": "مفتاح Groq غير موجود في ملف الإعدادات"})
                return

            history = load_memory()
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            messages.extend(history)

            if image:
                if not isinstance(image, str) or "," not in image:
                    self.send_json(400, {"error": "صيغة الصورة غير صحيحة"})
                    return

                header, encoded = image.split(",", 1)
                try:
                    image_bytes = base64.b64decode(encoded, validate=True)
                except Exception:
                    self.send_json(400, {"error": "تعذر قراءة الصورة"})
                    return

                if len(image_bytes) > MAX_IMAGE_BYTES:
                    self.send_json(413, {"error": "الصورة أكبر من 8 ميجابايت"})
                    return

                mime = detect_image_type(image_bytes)
                if not mime:
                    self.send_json(400, {"error": "استخدم JPG أو PNG أو WEBP"})
                    return

                data_url = "data:" + mime + ";base64," + base64.b64encode(image_bytes).decode("ascii")

                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question or "حلل الصورة واشرح ما يظهر فيها."},
                        {"type": "image_url", "image_url": {"url": data_url}}
                    ]
                })

                answer = send_request(messages, api_key, VISION_MODEL)

                history.append({
                    "role": "user",
                    "content": "أرسلت صورة وطلبت: " + (question or "تحليل الصورة")
                })

            else:
                messages.append({"role": "user", "content": question})
                answer = send_request(messages, api_key, TEXT_MODEL)
                history.append({"role": "user", "content": question})

            history.append({"role": "assistant", "content": answer})
            save_memory(history)

            self.send_json(200, {"answer": answer})

        except requests.RequestException as error:
            print("Groq connection error:", error)
            self.send_json(502, {"error": "حصلت مشكلة في اتصال Groq. جرّب مرة أخرى."})

        except Exception as error:
            print("Server error:", error)
            self.send_json(500, {"error": "حصل خطأ داخلي في الخادم."})


server = HTTPServer(("127.0.0.1", 8766), Handler)
print("MOHAB EL KING V3.2")
print("http://127.0.0.1:8766")
server.serve_forever()


