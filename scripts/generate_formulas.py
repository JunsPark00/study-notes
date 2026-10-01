#!/usr/bin/env python3
"""Render the original formula cards from this bundle's public TeX metadata.
Run: python scripts/generate_formulas.py
Requires matplotlib, pillow and Noto Sans CJK regular/bold fonts.
"""
import os, json, io, tempfile
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir())/'mpc-matplotlib'))
import matplotlib
matplotlib.use('Agg')
from matplotlib.mathtext import MathTextParser
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parent.parent/'content'
OUT=ROOT.parent/'docs'/'assets'/'formulas'
OUT.mkdir(exist_ok=True,parents=True)
REG=os.environ.get('MPC_FONT_REGULAR','/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
BOLD=os.environ.get('MPC_FONT_BOLD','/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')
D=json.loads((ROOT/'formulas.json').read_text())
ACCENTS=['#22577A','#355C7D','#087E8B','#466D3B','#74478C','#9A5B25','#365C9A','#A04C58']
def font(sz,bold=False): return ImageFont.truetype(BOLD if bold else REG,sz)
def wrap_px(text,f,maxw):
    # Wrap at words, then fall back to characters for a long unbroken run.
    dr=ImageDraw.Draw(Image.new('RGB',(4,4)))
    out=[]; line=''
    for word in text.split(' '):
        test=(line+' '+word).strip()
        if dr.textlength(test,font=f)>maxw and line:
            out.append(line);line=word
        else: line=test
    if line:out.append(line)
    return out

def math_img(s):
    b=io.BytesIO()
    prop=FontProperties(size=27, family='DejaVu Sans')
    expr='$'+s+'$'
    width,height,depth,_,_=MathTextParser('path').parse(expr,dpi=72,prop=prop)
    pad=10
    w=width+2*pad;h=height+2*pad
    fig=Figure(figsize=(w/72,h/72))
    fig.text(pad/w,(depth+pad)/h,expr,fontproperties=prop,color='#152638')
    fig.savefig(b,dpi=180,format='png',transparent=True)
    return Image.open(b).convert('RGBA')

def safe_note(s):
    return s.translate(str.maketrans({'₀':'0','₁':'1','₂':'2','₃':'3','₄':'4','₅':'5','₆':'6','₇':'7','₈':'8','₉':'9','⁺':'^+','⁻':'^−','⁴':'^4','ⁿ':'n'}))

manifest=[]
for idx,d in enumerate(D):
    W=1600; pad=84; inner=W-2*pad
    equations=[]
    for line in d['latex']:
        im=math_img(line)
        if im.width>inner-100:
            ratio=(inner-100)/im.width
            im=im.resize((round(im.width*ratio),round(im.height*ratio)),Image.Resampling.LANCZOS)
        equations.append(im)
    note_font=font(28)
    note_lines=[]
    for n in d['assumptions']:note_lines+=wrap_px(safe_note(n),note_font,inner-70)
    eq_gap=36
    eq_h=sum(im.height for im in equations)+eq_gap*(len(equations)-1)+104
    note_h=50+42*len(note_lines)
    H=220+eq_h+36+note_h+62
    canvas=Image.new('RGB',(W,H),'#FFFFFF');dr=ImageDraw.Draw(canvas)
    accent=ACCENTS[d['chapter']-1]
    dr.rounded_rectangle((pad,45,pad+196,91),radius=11,fill=accent)
    dr.text((pad+21,47),f'CHAPTER {d["chapter"]:02}',font=font(25,True),fill='white')
    dr.text((W-pad,52),'MPC · 핵심 수식',font=font(24),fill='#65768A',anchor='ra')
    dr.text((pad,119),d['title'],font=font(48,True),fill='#152638')
    box=(pad,220,W-pad,220+eq_h)
    dr.rounded_rectangle(box,radius=22,fill='#F4F7FA')
    dr.rounded_rectangle((pad,220,pad+8,220+eq_h),radius=4,fill=accent)
    y=220+52
    for im in equations:
        canvas.paste(im,((W-im.width)//2,y),im)
        y+=im.height+eq_gap
    ny=220+eq_h+36
    dr.text((pad,ny),'조건과 읽는 법',font=font(27,True),fill=accent)
    y=ny+49
    for n in note_lines:
        dr.text((pad+8,y),'· '+n,font=note_font,fill='#415269')
        y+=42
    dr.line((pad,H-41,W-pad,H-41),fill='#E1E7EF',width=2)
    dr.text((pad,H-33),'한국어 학습 노트의 핵심 식을 다시 조판한 보충 카드',font=font(19),fill='#7B8797')
    path=OUT/(d['id']+'.png');canvas.save(path,optimize=True)
    d.update(width=W,height=H)
    manifest.append(d)
    print(d['id'],(W,H))
print('DONE',len(manifest))
