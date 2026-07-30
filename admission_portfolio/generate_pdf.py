from __future__ import annotations

import os
from io import BytesIO
from pathlib import Path
from typing import Iterable

import requests
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

OUT = Path(__file__).with_name("Dong-You-Jyun-PCCU-Portfolio.pdf")
W, H = A4

NAVY = HexColor("#16263B")
NAVY2 = HexColor("#243A55")
CREAM = HexColor("#F5F1EA")
PAPER = HexColor("#FBFAF7")
RED = HexColor("#A95443")
SLATE = HexColor("#5D6874")
PALE = HexColor("#E6EBEF")
GOLD = HexColor("#C8B58B")
WHITE = colors.white
BLACK = HexColor("#1E252B")

pdfmetrics.registerFont(UnicodeCIDFont("MSung-Light"))
pdfmetrics.registerFont(UnicodeCIDFont("MHei-Medium"))
FONT = "MSung-Light"
BOLD = "MHei-Medium"

IMAGE_URLS = {
    "parade": "https://media.canva.com/v2/image-resize/format:JPG/height:200/quality:75/uri:ifs%3A%2F%2FM%2F6ac74011-9f95-4813-81db-b311a0a9707d/watermark:F/width:113?csig=AAAAAAAAAAAAAAAAAAAAAMF1qRygrGtxn3pFZfwAo2FFU6UVCo6aiMF-40wN462r&exp=1785411217&osig=AAAAAAAAAAAAAAAAAAAAAA4zFSajgAGIc0svgjp1xgXST31F1UdB1m-_UDYo-Bjj&signer=media-rpc&x-canva-quality=thumbnail",
    "camo": "https://media.canva.com/v2/image-resize/format:JPG/height:200/quality:75/uri:ifs%3A%2F%2FM%2F5db4ec05-1b18-43d4-9020-448ae742f0d5/watermark:F/width:158?csig=AAAAAAAAAAAAAAAAAAAAAJ_WX1CleC_WQpfrwKN1ulxvPL1vAZMXWCtQBTIn_duc&exp=1785411658&osig=AAAAAAAAAAAAAAAAAAAAAE0wMqvRt_j_fyfdvd2MqZW_2t9nCF7jFOQ7NzatjarV&signer=media-rpc&x-canva-quality=thumbnail",
    "preparatory": "https://media.canva.com/v2/image-resize/format:JPG/height:200/quality:75/uri:ifs%3A%2F%2FM%2Fe0e7695d-316b-4a9a-bc46-079627f568cf/watermark:F/width:151?csig=AAAAAAAAAAAAAAAAAAAAADE0RUhPKaF6xXQqMimgIWN6pZi-w0UMoGzB-LLaNukK&exp=1785410461&osig=AAAAAAAAAAAAAAAAAAAAAIZMW4Ypq69iQ8czbQ2otwfscqwg7Qll3RcPh5A-GHhB&signer=media-rpc&x-canva-quality=thumbnail",
    "academy": "https://media.canva.com/v2/image-resize/format:JPG/height:133/quality:75/uri:ifs%3A%2F%2FM%2F20d9f5a0-9bf2-4e74-aba6-55ec11334d89/watermark:F/width:200?csig=AAAAAAAAAAAAAAAAAAAAAMAAMOfn3P4IpNXo9rlNuZRjxoVwMQ3wj8I7_pZ1T9o5&exp=1785409377&osig=AAAAAAAAAAAAAAAAAAAAAPNmeHB4HNTUmM2iGSUA_hvyi0UVoUodPSe2V31uGry7&signer=media-rpc&x-canva-quality=thumbnail",
}


def fetch_images() -> dict[str, Image.Image]:
    result: dict[str, Image.Image] = {}
    for key, url in IMAGE_URLS.items():
        try:
            r = requests.get(url, timeout=20)
            r.raise_for_status()
            result[key] = Image.open(BytesIO(r.content)).convert("RGB")
        except Exception:
            img = Image.new("RGB", (800, 1000), (220, 225, 230))
            result[key] = img
    return result


def crop_image(img: Image.Image, target_ratio: float) -> Image.Image:
    w, h = img.size
    ratio = w / h
    if ratio > target_ratio:
        nw = int(h * target_ratio)
        left = (w - nw) // 2
        return img.crop((left, 0, left + nw, h))
    nh = int(w / target_ratio)
    top = max(0, (h - nh) // 2)
    return img.crop((0, top, w, top + nh))


def draw_image(c: canvas.Canvas, img: Image.Image, x: float, y: float, w: float, h: float, radius: float = 0) -> None:
    cropped = crop_image(img, w / h)
    if radius:
        c.saveState()
        p = c.beginPath()
        p.roundRect(x, y, w, h, radius)
        c.clipPath(p, stroke=0, fill=0)
        c.drawImage(ImageReader(cropped), x, y, w, h, preserveAspectRatio=False, mask="auto")
        c.restoreState()
    else:
        c.drawImage(ImageReader(cropped), x, y, w, h, preserveAspectRatio=False, mask="auto")


def wrap_text(text: str, font: str, size: float, max_width: float) -> list[str]:
    lines: list[str] = []
    for para in text.split("\n"):
        if not para:
            lines.append("")
            continue
        current = ""
        for ch in para:
            test = current + ch
            if pdfmetrics.stringWidth(test, font, size) <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = ch
        if current:
            lines.append(current)
    return lines


def text_box(c: canvas.Canvas, text: str, x: float, y_top: float, w: float, size: float = 10.5,
             leading: float = 16, font: str = FONT, color=BLACK, max_lines: int | None = None) -> float:
    c.setFont(font, size)
    c.setFillColor(color)
    y = y_top
    lines = wrap_text(text, font, size, w)
    if max_lines is not None:
        lines = lines[:max_lines]
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


def label(c: canvas.Canvas, text: str, x: float, y: float, fill=RED, text_color=WHITE, width: float | None = None) -> None:
    c.setFont(BOLD, 9)
    tw = pdfmetrics.stringWidth(text, BOLD, 9)
    ww = width or tw + 18
    c.setFillColor(fill)
    c.roundRect(x, y - 4, ww, 20, 10, fill=1, stroke=0)
    c.setFillColor(text_color)
    c.drawCentredString(x + ww / 2, y + 2, text)


def section_title(c: canvas.Canvas, title: str, subtitle: str | None = None) -> None:
    c.setFillColor(NAVY)
    c.rect(0, H - 88, W, 88, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.rect(42, H - 88, 8, 88, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont(BOLD, 24)
    c.drawString(68, H - 52, title)
    if subtitle:
        c.setFont(FONT, 9.5)
        c.setFillColor(HexColor("#D6DEE7"))
        c.drawRightString(W - 42, H - 52, subtitle)


def footer(c: canvas.Canvas, page: int) -> None:
    c.setStrokeColor(HexColor("#D8DDE1"))
    c.line(42, 34, W - 42, 34)
    c.setFont(FONT, 8)
    c.setFillColor(SLATE)
    c.drawString(42, 19, "中國文化大學進修學士班｜董宥均 書面審查資料")
    c.setFont(BOLD, 9)
    c.setFillColor(RED)
    c.drawRightString(W - 42, 19, f"{page:02d}")


def card(c: canvas.Canvas, x: float, y: float, w: float, h: float, title: str, body: str,
         accent=RED, body_size: float = 9.3) -> None:
    c.setFillColor(WHITE)
    c.setStrokeColor(HexColor("#D8DDE3"))
    c.roundRect(x, y, w, h, 9, fill=1, stroke=1)
    c.setFillColor(accent)
    c.roundRect(x, y + h - 32, w, 32, 9, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont(BOLD, 12)
    c.drawString(x + 14, y + h - 21, title)
    text_box(c, body, x + 14, y + h - 50, w - 28, size=body_size, leading=14.2, color=BLACK)


def bullet_list(c: canvas.Canvas, items: Iterable[str], x: float, y: float, w: float, size: float = 10.2,
                leading: float = 16) -> float:
    yy = y
    for item in items:
        c.setFillColor(RED)
        c.circle(x + 3, yy + 3, 2.6, fill=1, stroke=0)
        yy = text_box(c, item, x + 14, yy + 7, w - 14, size=size, leading=leading, color=BLACK)
        yy -= 4
    return yy


def build_pdf() -> None:
    images = fetch_images()
    c = canvas.Canvas(str(OUT), pagesize=A4)
    c.setTitle("董宥均｜中國文化大學進修學士班書面審查資料")

    # 1 Cover
    c.setFillColor(CREAM)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(NAVY)
    c.rect(0, 0, W * 0.61, H, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.rect(54, H - 134, 80, 5, fill=1, stroke=0)
    c.setFont(FONT, 11)
    c.setFillColor(HexColor("#D4DCE5"))
    c.drawString(54, H - 105, "115 學年度")
    c.setFillColor(WHITE)
    c.setFont(BOLD, 28)
    c.drawString(54, H - 180, "中國文化大學")
    c.setFont(BOLD, 26)
    c.drawString(54, H - 225, "進修學士班")
    c.setFont(BOLD, 30)
    c.drawString(54, H - 282, "書面審查資料")
    c.setFillColor(GOLD)
    c.setFont(BOLD, 34)
    c.drawString(54, H - 355, "董宥均")
    c.setFillColor(HexColor("#D4DCE5"))
    c.setFont(FONT, 10)
    c.drawString(54, H - 390, "中正預校畢業｜空軍官校就讀約兩年｜115 年 6 月離校")
    draw_image(c, images["academy"], W * 0.54, 265, W * 0.42, 280, radius=18)
    draw_image(c, images["parade"], W * 0.67, 67, W * 0.24, 180, radius=12)
    c.setFillColor(RED)
    c.roundRect(W * 0.59, 552, W * 0.34, 55, 12, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont(BOLD, 11)
    c.drawCentredString(W * 0.76, 580, "申請管道｜進修學士班暑假轉學招生")
    c.setFont(FONT, 8.5)
    c.drawCentredString(W * 0.76, 563, "個人經歷・自主學習・學習計畫")
    c.setFillColor(SLATE)
    c.setFont(FONT, 8)
    c.drawRightString(W - 42, 28, "申請人｜董宥均")
    c.showPage()

    # 2 Resume
    c.setFillColor(PAPER); c.rect(0, 0, W, H, fill=1, stroke=0)
    section_title(c, "個人簡歷", "PROFILE")
    draw_image(c, images["preparatory"], 42, 475, 148, 205, radius=10)
    c.setFillColor(NAVY)
    c.setFont(BOLD, 20)
    c.drawString(218, 676, "董宥均")
    label(c, "申請人", 218, 641, fill=RED)
    text_box(c, "113 年中正國防幹部預備學校畢業\n113 年進入空軍軍官學校\n115 年 6 月因其他職涯規劃離校\n申請中國文化大學進修學士班", 218, 615, 315, 10.8, 18)
    c.setFillColor(NAVY2); c.roundRect(42, 414, 511, 38, 9, fill=1, stroke=0)
    c.setFillColor(WHITE); c.setFont(BOLD, 12); c.drawString(56, 429, "教育歷程")
    timeline_y = 372
    events = [("113", "中正預校畢業"), ("113", "進入空軍官校與入伍訓"), ("113–115", "組訓組長、班長、文宣組"), ("115.06", "離校並重新規劃")]
    c.setStrokeColor(GOLD); c.setLineWidth(3); c.line(77, 207, 77, 373)
    for year, event in events:
        c.setFillColor(RED); c.circle(77, timeline_y, 6, fill=1, stroke=0)
        c.setFont(BOLD, 11); c.setFillColor(NAVY); c.drawString(98, timeline_y + 3, year)
        c.setFont(FONT, 10); c.setFillColor(BLACK); c.drawString(165, timeline_y + 3, event)
        timeline_y -= 48
    card(c, 315, 196, 238, 178, "幹部與團隊經歷",
         "全期班組訓組組長\n班長\n中隊文宣組\n\n工作內容包括：整理要求、安排分工、追蹤進度、人員掌握、現場補位、環境與資訊呈現。", accent=NAVY2)
    card(c, 42, 58, 511, 104, "目前方向",
         "正式工作經驗仍有限。入學後希望從行銷、內容、電商營運、業務或行政助理等基礎職務開始，白天累積實務，晚上完成學業，再依課程表現、作品品質與工作回饋確認專業方向。", accent=RED, body_size=10)
    footer(c, 2); c.showPage()

    # 3 Education narrative
    c.setFillColor(PAPER); c.rect(0, 0, W, H, fill=1, stroke=0)
    section_title(c, "求學經歷與自傳", "EDUCATION & AUTOBIOGRAPHY")
    draw_image(c, images["preparatory"], 42, 510, 154, 205, radius=10)
    draw_image(c, images["camo"], 215, 510, 154, 205, radius=10)
    draw_image(c, images["academy"], 388, 510, 165, 205, radius=10)
    captions = [(42, "中正預校｜規律與團體生活"), (215, "入伍訓｜適應壓力與任務"), (388, "空軍官校｜幹部與責任")]
    for x, t in captions:
        c.setFont(FONT, 8.2); c.setFillColor(SLATE); c.drawString(x, 495, t)
    c.setFillColor(NAVY)
    c.setFont(BOLD, 16)
    c.drawString(42, 453, "在制度中形成的做事方式")
    body = (
        "113 年自中正國防幹部預備學校畢業後，我進入空軍軍官學校。軍事教育讓我很早接觸固定作息、明確標準與團體責任。"
        "我逐漸理解，可靠不是自己覺得有努力，而是時間、資訊與結果都能讓別人再次確認。集合前確認人員，任務開始前確認要求，完成後主動回報，這些看似普通的動作，少一個就可能影響整個團體。\n\n"
        "入伍訓與官校生活也讓我看見自己的不足。我不是一開始就懂得帶人，也曾以為把話說完就是完成溝通。真正遇到進度落差、理解不同或現場缺口時，我才知道，責任不只是把自己的部分做完，而是確保事情能繼續往前。"
    )
    text_box(c, body, 42, 425, 511, 10.5, 17)
    c.setFillColor(PALE); c.roundRect(42, 104, 511, 92, 8, fill=1, stroke=0)
    c.setFillColor(NAVY); c.setFont(BOLD, 12); c.drawString(58, 170, "我保留下來的習慣")
    bullet_list(c, ["開始前確認目的、時間與完成標準", "有變動提早說明，不把問題拖到最後", "完成後主動回報，讓下一個人知道如何接手", "結果不理想時，先檢查自己的安排"], 58, 148, 475, size=9.5, leading=14)
    footer(c, 3); c.showPage()

    # 4 Leadership
    c.setFillColor(PAPER); c.rect(0, 0, W, H, fill=1, stroke=0)
    section_title(c, "幹部經驗", "LEADERSHIP")
    draw_image(c, images["parade"], 410, 528, 143, 208, radius=10)
    card(c, 42, 505, 338, 232, "全期班組訓組組長",
         "實際工作\n接收要求、整理資訊、安排分工、追蹤進度，並在同學與長官之間溝通。\n\n我的做法\n先確認目的、期限與完成標準，再將內容轉成組員能理解的下一步；出現落差時，先檢查分工與資訊是否清楚，再補上缺口並完成回報。", accent=NAVY2, body_size=9.1)
    card(c, 42, 255, 244, 220, "班長",
         "工作包含點名、人員掌握、整隊、移動與交辦事項回報。這個角色讓我養成先確認事實、再採取行動的順序；現場有缺口時先補位，完成後主動回報。", accent=RED, body_size=9.4)
    card(c, 309, 255, 244, 220, "中隊文宣組",
         "參與環境佈置與視覺呈現，也曾製作生日牆。我開始注意文字、位置、閱讀順序與使用情境。這段經驗成為後來接觸品牌內容與數位溝通的起點。", accent=GOLD, body_size=9.4)
    c.setFillColor(NAVY); c.setFont(BOLD, 13); c.drawString(42, 216, "我從三種角色學到的事")
    bullet_list(c, ["領導不是把責任往下分，而是對最後結果保有責任", "基礎工作越普通，越不能靠印象與猜測", "設計不只是好看，也要讓對方快速理解與採取行動"], 42, 192, 511, size=9.8, leading=15)
    footer(c, 4); c.showPage()

    # 5 Motivation
    c.setFillColor(PAPER); c.rect(0, 0, W, H, fill=1, stroke=0)
    section_title(c, "重要轉折與申請動機", "MOTIVATION")
    c.setFillColor(NAVY2); c.roundRect(42, 610, 511, 122, 12, fill=1, stroke=0)
    c.setFillColor(WHITE); c.setFont(BOLD, 14); c.drawString(60, 702, "其他職涯規劃")
    turn = (
        "在空軍官校就讀期間，我逐漸更清楚自己的興趣與長期發展方向。經過評估後，我決定依照其他職涯規劃離開原有道路，重新安排升學與未來發展。這項選擇不代表否定軍校經歷，而是開始對下一階段的選擇負責。"
    )
    text_box(c, turn, 60, 674, 475, 10.4, 17, color=WHITE)
    card(c, 42, 375, 244, 200, "為什麼需要大學教育",
         "自主學習讓我能開始做企劃與工具，但缺少商管、財務、消費者理解、外語與數位應用的系統基礎。我需要課程、教師回饋與同儕合作，讓作品不只停在第一版。", accent=RED, body_size=9.4)
    card(c, 309, 375, 244, 200, "為什麼選擇進修學士班",
         "我希望白天累積工作現場的經驗，晚上完成學業。工作可以讓我理解顧客、主管與組織；課程則能補足理論，讓兩邊互相驗證。", accent=NAVY2, body_size=9.4)
    card(c, 42, 150, 511, 190, "為什麼是中國文化大學",
         "進修學士班的學習型態符合我的半工半讀規劃，也提供商學、管理、外語與實務相關課程。入學後，我會先建立基礎，再比較課程投入、專題品質、工作連結與師長建議，依學校規定選擇適合的專業方向。", accent=GOLD, body_size=10)
    footer(c, 5); c.showPage()

    # 6 Projects
    c.setFillColor(PAPER); c.rect(0, 0, W, H, fill=1, stroke=0)
    section_title(c, "自主學習與作品", "PROJECTS")
    card(c, 42, 520, 511, 215, "商家短影音內容工作簿｜自主練習／產品原型",
         "問題背景：小型商家常知道短影音重要，卻缺少固定流程。\n我的角色：整理品牌、受眾、內容題目、腳本、發布檢查與成效紀錄。\n實際產出：可編輯工作簿與操作步驟。\n限制：尚無付費客戶、營收或真實發布數據。\n下一步：找實際使用者測試並依使用紀錄修正。", accent=NAVY2, body_size=9.1)
    card(c, 42, 285, 244, 205, "PILATIQUE 品牌與預約提案",
         "類型：依公開資訊完成的提案作品。\n內容：品牌定位、IG 資訊架構、FAQ、LINE 首輪詢問與預約前溝通。\n限制：並非正式合作或已導入方案。\n反思：行銷不只要有質感，也要幫助新客做決定。", accent=RED, body_size=8.9)
    card(c, 309, 285, 244, 205, "樂沐板橋鍍膜中心健檢",
         "類型：公開資訊分析。\n內容：IG 首頁、LINE 問答、服務選擇與預約流程。\n限制：沒有內部資料、付費交付或導入成效。\n反思：建議是否有效，仍需要實際使用與數據驗證。", accent=GOLD, body_size=8.9)
    c.setFillColor(PALE); c.roundRect(42, 104, 511, 145, 10, fill=1, stroke=0)
    c.setFillColor(NAVY); c.setFont(BOLD, 12); c.drawString(58, 221, "AI 工具的使用原則")
    bullet_list(c, ["AI 協助整理資料、延伸題目與產生初稿", "選題、事實判斷、欄位邏輯、文字修正與成果限制由本人負責", "未驗證的客戶成果、營收、合作關係與能力程度不寫入備審"], 58, 196, 475, size=9.4, leading=14.5)
    footer(c, 6); c.showPage()

    # 7 Plan and attachments
    c.setFillColor(PAPER); c.rect(0, 0, W, H, fill=1, stroke=0)
    section_title(c, "學習計畫與附件索引", "PLAN & APPENDIX")
    phases = [
        ("入學前", "確認學分抵免與畢業條件；補強試算表、簡報、基本商學與英文；整理作品原始檔。", "報名文件與作品版本紀錄"),
        ("在學初期", "維持出席與課業；尋找行銷、電商、內容、業務或行政助理等基礎職務。", "成績紀錄與第一份課堂作品"),
        ("在學中後期", "把工作中的顧客溝通、內容或流程問題轉成課堂專題；保留初稿、回饋與修正版。", "每學期至少一項可驗證成果"),
        ("畢業後", "朝行銷企劃、數位內容、品牌營運、商業開發或相關方向發展，從基礎職務累積能力。", "完整作品集與可持續職涯方向"),
    ]
    y = 674
    for i, (phase, action, output) in enumerate(phases, start=1):
        c.setFillColor(RED if i % 2 else NAVY2)
        c.circle(65, y + 14, 17, fill=1, stroke=0)
        c.setFillColor(WHITE); c.setFont(BOLD, 11); c.drawCentredString(65, y + 10, f"{i}")
        c.setFillColor(NAVY); c.setFont(BOLD, 13); c.drawString(98, y + 22, phase)
        c.setFont(FONT, 9.5); c.setFillColor(BLACK); text_box(c, action, 98, y + 2, 455, 9.5, 14)
        c.setFont(BOLD, 9); c.setFillColor(RED); c.drawString(98, y - 43, "預期成果")
        c.setFont(FONT, 9); c.setFillColor(SLATE); c.drawString(158, y - 43, output)
        y -= 132
    c.setFillColor(PALE); c.roundRect(42, 115, 511, 128, 10, fill=1, stroke=0)
    c.setFillColor(NAVY); c.setFont(BOLD, 12); c.drawString(58, 217, "驗收方式")
    c.setFont(FONT, 9.5); c.setFillColor(BLACK)
    c.drawString(58, 195, "出席與成績｜工作紀錄｜作品版本｜教師與同儕回饋｜能否穩定維持半工半讀")
    c.setFont(BOLD, 12); c.setFillColor(NAVY); c.drawString(58, 166, "附件索引")
    c.setFont(FONT, 9.3); c.setFillColor(BLACK)
    c.drawString(58, 145, "【待補】歷年成績單　【待補】空軍官校修業／離校證明")
    c.drawString(58, 127, "【待補】中正預校畢業證明　【待補】幹部或活動佐證")
    c.setFillColor(RED); c.setFont(BOLD, 12); c.drawString(42, 79, "我希望用後續的成績、工作與作品，證明這次選擇能被長期完成。")
    footer(c, 7); c.showPage()

    c.save()
    print(f"Created {OUT}")


if __name__ == "__main__":
    build_pdf()
