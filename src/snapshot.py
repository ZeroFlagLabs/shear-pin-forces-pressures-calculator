"""Print-friendly calculation report; shared by clipboard and PNG."""
from datetime import datetime
from PySide6.QtCore import Qt,QRectF
from PySide6.QtGui import QColor,QFont,QFontMetrics,QPainter,QPen,QPixmap
from calculation_data import result_text
W,H=790,420
INK,MUTED,BLUE,RULE="#243D58","#657A91","#164F8A","#D8E1EA"
TITLE="Shear Pin Forces & Pressures Calculator"

def render_snapshot(data,timestamp=None):
    if data is None:raise ValueError("A valid shear force calculation is required.")
    timestamp=timestamp or datetime.now()
    image=QPixmap(W*2,H*2);image.fill(QColor("white"))
    p=QPainter(image);p.scale(2,2)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    def text(x,y,w,h,value,*,size=12,bold=False,colour=INK,align="left"):
        f=QFont("Segoe UI");f.setPixelSize(size)
        f.setWeight(QFont.Weight.DemiBold if bold else QFont.Weight.Normal)
        value=str(value)
        while QFontMetrics(f).horizontalAdvance(value)>w and f.pixelSize()>7:f.setPixelSize(f.pixelSize()-1)
        if QFontMetrics(f).horizontalAdvance(value)>w:raise ValueError("Report text too wide: "+value)
        p.setFont(f);p.setPen(QColor(colour))
        flags={"left":Qt.AlignmentFlag.AlignLeft,"right":Qt.AlignmentFlag.AlignRight}[align]|Qt.AlignmentFlag.AlignVCenter
        p.drawText(QRectF(x,y,w,h),int(flags),value)
    def line(y,x1=24,x2=W-24):
        p.setPen(QPen(QColor(RULE),.9));p.drawLine(QRectF(x1,y,x2-x1,0).topLeft(),QRectF(x1,y,x2-x1,0).topRight())
    def heading(x,y,w,value):text(x,y,w,22,value,size=14,bold=True,colour=BLUE)
    def pair(x,y,w,label,value,lw=115):
        text(x,y,lw,24,label,colour=MUTED)
        text(x+lw+5,y,w-lw-5,24,value,bold=True,align="right")
    try:
        p.setPen(QPen(QColor("#9FBBD5"),1));p.drawRect(QRectF(5,5,W-11,H-11))
        text(24,13,535,36,TITLE,size=22,bold=True,colour=BLUE)
        text(560,16,206,30,timestamp.strftime("%d %b %Y  %H:%M")+"  |  v2.0.0",size=11,colour=MUTED,align="right")
        line(57)
        heading(24,68,350,"CONFIGURATION")
        pair(24,93,350,"Number of pins",data.pins,145)
        pair(24,117,350,"Shear planes per pin",data.planes,145)
        pair(24,141,350,"Shear strength factor",f"{data.factor:g}",145)
        heading(406,68,360,"SHEAR PIN INPUTS")
        for i,r in enumerate(data.inputs[:2]):pair(406,93+24*i,360,r.name,r.display(),102)
        line(175)
        heading(24,185,350,"PRESSURE INPUTS (OPTIONAL)")
        for i,r in enumerate(data.inputs[2:]):pair(24,210+24*i,350,r.name,r.display(),102)
        heading(406,185,360,"CALCULATION BASIS")
        text(406,210,360,24,f"Shear strength = {data.factor:g} \u00d7 UTS")
        text(406,234,360,24,"Identical pins and equal load sharing assumed.")
        line(269)
        heading(24,279,300,"RESULTS")
        text(350,279,195,22,"Minimum",size=12,bold=True,colour=BLUE,align="right")
        text(566,279,200,22,"Maximum",size=12,bold=True,colour=BLUE,align="right")
        line(306)
        for i,(name,attr,unit) in enumerate((("Shear force","force","lbf"),("Shear pressure","pressure","psi"))):
            y=311+i*36
            text(24,y,300,34,name,size=14,bold=True)
            text(350,y,195,34,result_text(getattr(data.minimum,attr),unit),size=16,bold=True,colour=BLUE,align="right")
            text(566,y,200,34,result_text(getattr(data.maximum,attr),unit),size=16,bold=True,colour=BLUE,align="right")
            line(y+34)
        note=data.pressure_note if data.minimum.pressure is None else "Pressure uses minimum force / maximum area and maximum force / minimum area."
        text(24,391,W-48,18,note,size=11,colour=MUTED)
    finally:p.end()
    return image
