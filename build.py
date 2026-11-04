#!/usr/bin/env python3
"""يولّد index.html (مُعمّى النص) من index.src.html (المقروء).

الاستخدام:  python3 build.py
- نصوص الصفحة (داخل <body>) تُخزَّن مشفّرة (XOR + Base64) وتُعرض بالجافاسكربت وقت التحميل.
- هذا ردع للنسخ السريع ولعرض المصدر، وليس حماية حقيقية: لقطة الشاشة وأدوات المطوّر تتجاوزه.
- لا يشمل: <title> ووسم description (لازمان للمشاركة)، ونصوص alt وaria-label (للإتاحة)، وروابط tel:.
- لا تستخدمه في الموقع الكامل: يضرّ بالأرشفة وبقارئات الشاشة عند تعطّل الجافاسكربت.
"""
import base64, json, re, sys, pathlib

KEY = "DAF-2026-Ω#7"          # مفتاح XOR (ثابت لتكون المخرجات قابلة للمقارنة)
SRC = pathlib.Path(__file__).with_name("index.src.html")
OUT = pathlib.Path(__file__).with_name("index.html")

src = SRC.read_text(encoding="utf-8")
b0 = src.index("<body>") + len("<body>")
b1 = src.index("<noscript>")              # ما بعده (noscript والسكربتات) يبقى كما هو
head, region, tail = src[:b0], src[b0:b1], src[b1:]

kb = KEY.encode("utf-8")
store = []

def enc(s: str) -> str:
    raw = s.encode("utf-8")
    return base64.b64encode(bytes(b ^ kb[i % len(kb)] for i, b in enumerate(raw))).decode("ascii")

def repl(m):
    text = m.group(1)
    if not text.strip():
        return m.group(0)
    lead = text[: len(text) - len(text.lstrip())]
    trail = text[len(text.rstrip()):]
    core = text.strip()
    store.append(enc(core))
    return f'>{lead}<span data-o="{len(store) - 1}"></span>{trail}<'

region = re.sub(r">([^<>]+)<", repl, region)

decoder = (
    "<script>(function(){var K=" + json.dumps(KEY, ensure_ascii=True) + ",D=" + json.dumps(store) + ";"
    "var kb=new TextEncoder().encode(K);"
    "function d(s){var b=atob(s),u=new Uint8Array(b.length);for(var i=0;i<b.length;i++)u[i]=b.charCodeAt(i)^kb[i%kb.length];return new TextDecoder().decode(u)}"
    "[].forEach.call(document.querySelectorAll('[data-o]'),function(e){e.textContent=d(D[+e.getAttribute('data-o')])})})();</script>"
)
tail = tail.replace("<!--OBF-->", decoder, 1)

OUT.write_text(head + region + tail, encoding="utf-8")
print(f"built {OUT.name}: {len(store)} text nodes obfuscated, {OUT.stat().st_size} bytes")
