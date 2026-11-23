"""Capture the actual interface across frequencies, key chart modes and mobile."""
import json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
OUT=Path(os.environ.get('SCREENSHOT_DIR','verification/browser'));OUT.mkdir(parents=True,exist_ok=True)
url=os.environ.get('DASHBOARD_URL','http://127.0.0.1:8501')
(OUT/'checks.json').write_text(json.dumps({'url':url,'requested_source_commit':os.environ.get('GITHUB_SHA'),'status':'running'},indent=2))
with sync_playwright() as p:
    browser=p.chromium.launch();page=browser.new_page(viewport={'width':1440,'height':1100},device_scale_factor=1)
    page.goto(url,wait_until='domcontentloaded',timeout=90000);ui=None
    for attempt in range(90):
        for frame in page.frames:
            if frame.get_by_text('Economic activity',exact=True).count():ui=frame;break
        if ui is not None:break
        page.wait_for_timeout(500)
    if ui is None:
        page.screenshot(path=str(OUT/'load-failure.png'),full_page=True)
        raise RuntimeError('Updated dashboard did not render; diagnostic screenshot saved')
    ui.locator('.js-plotly-plot').first.wait_for(timeout=60000);page.wait_for_timeout(1500)
    errors=[]
    def capture(name,heading):
        ui.get_by_text(heading,exact=True).first.evaluate('(el)=>el.scrollIntoView({block: "center"})');page.wait_for_timeout(600)
        errors.extend(ui.locator('[data-testid="stException"]').all_text_contents())
        page.screenshot(path=str(OUT/(name+'.png')),full_page=True)
    def wait_text(locator,name):
        try:locator.get_by_text(name,exact=False).first.wait_for(state='visible',timeout=30000)
        except Exception:
            page.screenshot(path=str(OUT/'interaction-failure.png'),full_page=True)
            raise
    def click(name):ui.get_by_text(name,exact=True).first.click();page.wait_for_timeout(1000)
    capture('macro-monthly-top','Economic activity');capture('macro-monthly-bottom','Employment')
    click('Quarterly');capture('macro-quarterly-top','Economic activity');capture('macro-quarterly-bottom','Employment')
    capture('fx-references','Exchange rates')
    click('Annual');capture('macro-annual-top','Economic activity');capture('macro-annual-bottom','Employment')
    click('Quarterly')
    ui.get_by_role('button',name='Expand / customize',exact=True).first.click();page.wait_for_timeout(1200)
    ui.get_by_role('dialog').get_by_text('Monthly',exact=True).click();page.wait_for_timeout(800)
    wait_text(ui.get_by_role('dialog'),'Total IMACEC')
    ui.get_by_role('dialog').get_by_text('Quarterly',exact=True).click();page.wait_for_timeout(800)
    wait_text(ui.get_by_role('dialog'),'Total GDP')
    ui.get_by_role('dialog').get_by_text('Annual',exact=True).click();page.wait_for_timeout(800)
    wait_text(ui.get_by_role('dialog'),'Total GDP')
    capture('expanded-annual','Expanded chart workspace')
    ui.get_by_role('dialog').get_by_text('Quarterly',exact=True).click();page.wait_for_timeout(800)
    ui.get_by_label('Left axis',exact=True).click();ui.get_by_role('option',name='Custom range',exact=True).click();page.wait_for_timeout(600)
    ui.get_by_label('Left axis minimum',exact=True).fill('-1');ui.get_by_label('Left axis minimum',exact=True).press('Enter');page.wait_for_timeout(600)
    ui.get_by_label('Left axis maximum',exact=True).fill('1');ui.get_by_label('Left axis maximum',exact=True).press('Enter');page.wait_for_timeout(600)
    wait_text(ui,'selected observations fall outside')
    capture('expanded-activity','Expanded chart workspace')
    (OUT/'dialog-dimensions.json').write_text(json.dumps(ui.locator('[role=dialog]').evaluate_all('(els)=>els.map(e=>({width:e.clientWidth,scroll:e.scrollWidth,parentWidth:e.parentElement.clientWidth,html:e.parentElement.outerHTML.slice(0,500)}))')))
    assert ui.locator('[role=dialog]').evaluate('(e)=>e.clientWidth <= e.parentElement.clientWidth'), 'Dialog overflows parent'
    ui.get_by_role('button',name='Close',exact=True).click();page.wait_for_timeout(600)
    click('Monthly');click('Retail outlook');capture('retail-monthly-top','Retail sales - real growth');capture('retail-monthly-bottom','Retail channels')
    capture('retail-online-growth','Online versus in-store')
    ui.get_by_role('radiogroup',name='Online / in-store measure').get_by_text('Online penetration',exact=True).click();page.wait_for_timeout(800)
    capture('retail-online-penetration','Online versus in-store')
    click('Sales growth')
    ui.get_by_role('radiogroup',name='Channel measure').get_by_text('Online penetration',exact=True).click();page.wait_for_timeout(800)
    capture('retail-channel-penetration','Retail channels')
    click('Quarterly');capture('retail-quarterly-top','Retail sales - real growth');capture('retail-quarterly-bottom','Retail channels')
    click('Annual');capture('retail-annual-top','Retail sales - real growth');capture('retail-annual-bottom','Retail channels')
    click('Monthly');click('Macroeconomic outlook')
    ui.get_by_label('From year',exact=True).fill('2007');ui.get_by_role('option',name='2007',exact=True).click();page.wait_for_timeout(700)
    ui.get_by_label('From month',exact=True).click();ui.get_by_role('option',name='Jan',exact=True).click();page.wait_for_timeout(700)
    capture('macro-full-history','Economic activity')
    page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(1000)
    capture('mobile-macro','Economic activity');capture('mobile-employment','Employment')
    (OUT/'checks.json').write_text(json.dumps({'url':url,'status':'passed','requested_source_commit':os.environ.get('GITHUB_SHA'),'frequencies':['Monthly','Quarterly','Annual'],'history':'Period selector and expanded chart workspace','chart_modes_checked':True,'exceptions':errors},indent=2))
    assert not errors,errors
    browser.close()
