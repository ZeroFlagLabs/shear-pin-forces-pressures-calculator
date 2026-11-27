"""Shear pin inspector. Qt rich text format adapted from the ZFL O-ring inspector."""
from html import escape
from dataclasses import dataclass
import math
from pathlib import Path
from dialog_theme import apply_dialog_theme, return_focus_after_selection
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile,QIODevice
from PySide6.QtWidgets import QTextBrowser,QComboBox,QPushButton,QLabel,QTabWidget
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

def _math(text):
    """Escaped, readable equation text; fractions use Qt's HTML table engine."""
    return escape(text).replace('  ', '&nbsp;&nbsp;')


def _math_equation(expression, fraction):
    """Use 10 pt for equations and fractions, matching the dimension inputs."""
    if fraction is None:
        return ('<p style="margin:3px 0 3px 14px;font-size:10pt;color:#242424;">'
                + _math(expression) + '</p>')
    lhs, numer, denom, suffix = fraction
    return ('<table cellspacing="0" cellpadding="0" style="margin-left:13px;">'
            '<tr><td rowspan="3" valign="middle" style="font-size:10pt;">'
            + _math(lhs) + '&nbsp;=&nbsp;</td>'
            '<td align="center" style="font-size:10pt;padding:0 5px;">'
            + _math(numer) + '</td>'
            '<td rowspan="3" valign="middle" style="font-size:10pt;">'
            + '&nbsp;' + _math(suffix) + '</td></tr>'
            '<tr><td><hr style="height:1px;color:#385a78;"/></td></tr>'
            '<tr><td align="center" style="font-size:10pt;padding:0 5px;">'
            + _math(denom) + '</td></tr></table>')


def _section_rule():
    """An understated divider separating the three Inspector sections."""
    return '<hr style="color:#D8E1EA;background-color:#D8E1EA;height:1px;"/>'



@dataclass
class Step:
    title:str
    symbolic:str
    numeric:str
    result:float
    unit:str=""
    symbol_fraction:tuple|None=None
    numeric_fraction:tuple|None=None
    note:str=""

def case_steps(data,key,places=3):
    c=getattr(data,key)
    n=lambda x:f"{x:.{places}f}"
    dims=[("Number of pins",str(data.pins),""),
          ("Shear planes per pin",str(data.planes),""),
          ("Shear strength factor",str(data.factor),""),
          ("Material UTS used",n(c.uts),"psi"),
          ("Pin diameter used",n(c.diameter),"in")]
    steps=[]
    def add(title,sym,num,value,unit="",sf=None,nf=None,note=""):
        steps.append(Step(title,sym,num,value,unit,sf,nf,note))
    def frac(title,lhs,num,den,nnum,nden,value,unit="",note=""):
        add(title,"","",value,unit,(lhs,num,den,""),(lhs,nnum,nden,""),note)
    add("Shear strength","\u03c4 = k \u00d7 UTS",f"\u03c4 = {data.factor:g} \u00d7 {n(c.uts)}",c.strength,"psi")
    frac("Pin cross-sectional area","A\u209a","\u03c0 \u00d7 d\u00b2","4",f"\u03c0 \u00d7 {n(c.diameter)}\u00b2","4",c.pin_area,"in\u00b2")
    add("Total effective shear area","A\u209b = N\u209a \u00d7 N\u209b \u00d7 A\u209a",f"A\u209b = {data.pins} \u00d7 {data.planes} \u00d7 {n(c.pin_area)}",c.shear_area,"in\u00b2")
    add("Shear force","F = \u03c4 \u00d7 A\u209b",f"F = {n(c.strength)} \u00d7 {n(c.shear_area)}",c.force,"lbf")
    if c.pressure is not None:
        dims.extend([("Annulus OD used",n(c.od),"in"),("Annulus ID used",n(c.id),"in")])
        frac("Effective annulus area","A","\u03c0 \u00d7 (OD\u00b2 \u2212 ID\u00b2)","4",
             f"\u03c0 \u00d7 ({n(c.od)}\u00b2 \u2212 {n(c.id)}\u00b2)","4",c.annulus,"in\u00b2",
             note="Maximum area governs minimum pressure." if key=="minimum" else "Minimum area governs maximum pressure.")
        frac("Shear pressure","P","F","A",n(c.force),n(c.annulus),c.pressure,"psi")
    return dims,steps

def html_breakdown(data,key,places):
    from calculation_data import result_text
    c=getattr(data,key);dims,steps=case_steps(data,key,places)
    heading=key.capitalize()+" shear force: "+result_text(c.force,"lbf")
    if c.pressure is not None:
        pressure_heading=key.capitalize()+" shear pressure: "+result_text(c.pressure,"psi")
        pressure_html='<p style="font-size:12pt;color:#164f8a;margin:3px 0 4px 0;"><b>'+escape(pressure_heading)+'</b></p>'
    else:
        pressure_html=''
    lines=['<html><body style="font-family:Segoe UI,Arial,sans-serif;color:#242424;font-size:10pt;">',
           '<p style="font-size:12pt;color:#164f8a;margin:3px 0 4px 0;"><b>'+escape(heading)+'</b></p>',
           pressure_html,
           _section_rule(),'<p style="font-size:10pt;margin:13px 0 18px 0;color:#164f8a;"><b>Input Values</b></p>',
           '<p style="font-size:1pt;margin:0 0 12px 0;">&nbsp;</p>',
           '<table cellspacing="0" cellpadding="3" width="100%" style="font-size:10pt;">']
    for label,value,unit in dims:
        lines.append('<tr><td>'+escape(label)+'</td><td align="right">'+escape(value+(" "+unit if unit else ""))+'</td></tr>')
    lines += ['</table>','<p style="font-size:1pt;margin:0 0 12px 0;">&nbsp;</p>',_section_rule(),
              '<p style="font-size:10pt;margin:13px 0 13px 0;color:#164f8a;"><b>Calculation Breakdown</b></p>']
    for i,s in enumerate(steps,1):
        lines += ['<p style="font-size:10pt;margin:18px 0 7px 0;color:#164f8a;"><b>'+str(i)+'. '+escape(s.title)+'</b></p>',
                  _math_equation(s.symbolic,s.symbol_fraction),
                  '<p style="font-size:9pt;color:#667c94;margin:6px 0 4px 13px;">Substitution</p>',
                  _math_equation(s.numeric,s.numeric_fraction),
                  '<p style="font-size:10pt;margin:7px 0 3px 13px;color:#164f8a;"><b>Result: '+f'{s.result:.{places}f}'+(' '+escape(s.unit) if s.unit else '')+'</b></p>']
        if s.note:lines.append('<p style="font-size:9pt;margin:5px 0 12px 13px;color:#667c94;">'+escape(s.note)+'</p>')
    lines.append('<p style="font-size:9pt;color:#667c94;margin:12px 0 8px 13px;">Identical pins and equal load sharing across shear planes are assumed. Shear strength is estimated as the selected factor multiplied by UTS.</p>')
    if c.pressure is None:lines.append('<p style="font-size:9pt;color:#667c94;margin:12px 0 8px 13px;">'+escape(data.pressure_note)+'</p>')
    return '\n'.join(lines+['</body></html>'])

def build_inspect_results(data,parent):
    f=QFile(str(Path(__file__).parent/"ui/inspect_results.ui"))
    if not f.open(QIODevice.OpenModeFlag.ReadOnly):raise RuntimeError("Inspector form missing")
    loader=QUiLoader()
    try:dialog=loader.load(f,parent)
    finally:f.close()
    dialog.setParent(parent,dialog.windowFlags())
    dialog.setWindowIcon(parent.windowIcon())
    dialog.setFont(QFont("Segoe UI",9))
    dialog.setStyleSheet("""
        QPushButton {background:#eaf3fc;color:#144b83;border:1px solid #9ebfe2;border-radius:5px;min-height:24px;padding:2px 8px;font-weight:600;}
        QPushButton:hover {background:#d9ecff;}
        QFrame#inspect_heading_rule {color:#858585;}
        QTabWidget::pane {background:white;border:1px solid #e7e7e7;border-radius:4px;}
        QTabBar::tab {background:#f1f1f1;border:1px solid #e5e5e5;border-top-left-radius:5px;border-top-right-radius:4px;padding:4px 11px;color:#344556;}
        QTabBar::tab:selected {background:white;color:#1b3452;border-bottom-color:white;}
        QTextBrowser {background:white;border:1px solid #e7e7e7;border-radius:4px;color:#242424;}
        QComboBox {background:white;border:1px solid #b9cce1;border-radius:4px;min-height:22px;padding:1px 4px;color:#243d58;}
        QComboBox:focus {border:2px solid #258aca;padding:0px 3px;}
        """)
    controls={}
    for key in ("minimum","maximum"):
        precision=dialog.findChild(QComboBox,key+"_precision")
        browser=dialog.findChild(QTextBrowser,key+"_text")
        precision.setMaxVisibleItems(7)
        precision.setFixedSize(210,26)
        precision.addItems([f"{x} DP" for x in range(7)])
        precision.setCurrentIndex(3)
        browser.setOpenExternalLinks(False)
        controls[key]=(precision,browser)
    def redraw(places):
        for precision,browser in controls.values():
            blocked=precision.blockSignals(True);precision.setCurrentIndex(places);precision.blockSignals(blocked)
        for key,(_,browser) in controls.items():
            pos=browser.verticalScrollBar().value()
            html=html_breakdown(data,key,places)
            browser.setHtml(html)
            browser.verticalScrollBar().setValue(pos)
    for combo, browser in controls.values():
        combo.currentIndexChanged.connect(redraw)
        return_focus_after_selection(combo, browser)
    close=dialog.findChild(QPushButton,"close_inspection")
    close.setFixedSize(106,30);close.clicked.connect(dialog.accept)
    redraw(3)
    apply_dialog_theme(dialog)
    return dialog
