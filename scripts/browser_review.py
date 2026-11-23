"""Real Chromium screenshots and interaction checks for visual review."""
import json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
OUT=Path(os.environ.get('SCREENSHOT_DIR','verification/browser'));OUT.mkdir(parents=True,exist_ok=True)
url=os.environ.get('DASHBOARD_URL','http://127.0.0.1:8501')
with sync_playwright() as p:
    browser=p.chromium.launch()
    page=browser.new_page(viewport={'width':1440,'height':1100},device_scale_factor=1)
    page.goto(url,wait_until='domcontentloaded',timeout=90000)
    ui=None
    for attempt in range(60):
        for frame in page.frames:
            if frame.get_by_text('Economic activity',exact=True).count():
                ui=frame;break
        if ui is not None: break
        page.wait_for_timeout(500)
    if ui is None:
        page.screenshot(path=str(OUT/'load-failure.png'),full_page=True)
        (OUT/'load-failure.json').write_text(json.dumps({'url':page.url,'frames':[f.url for f in page.frames],'text':page.locator('body').inner_text()},indent=2))
        raise RuntimeError('Dashboard not rendered; diagnostic screenshot saved')
    ui.locator('.js-plotly-plot').first.wait_for(timeout=60000)
    page.wait_for_timeout(2500)
    def capture(name):
        page.screenshot(path=str(OUT/(name+'.png')),full_page=True)
    capture('macro-top')
    ui.get_by_text('Employment',exact=True).scroll_into_view_if_needed()
    capture('macro-bottom')
    ui.get_by_label('History',exact=True).click()
    ui.get_by_role('option',name='Since 2018',exact=True).click()
    page.wait_for_timeout(1200)
    ui.get_by_text('Economic activity',exact=True).scroll_into_view_if_needed()
    capture('macro-since-2018')
    ui.get_by_text('Retail outlook',exact=True).click()
    ui.get_by_text('Consumer demand',exact=True).wait_for()
    page.wait_for_timeout(2000)
    ui.get_by_text('Latest signals',exact=True).scroll_into_view_if_needed()
    capture('retail-top')
    ui.get_by_text('Retail channels',exact=True).scroll_into_view_if_needed()
    capture('retail-bottom')
    ui.get_by_text('Macroeconomic outlook',exact=True).click()
    ui.get_by_text('Economic activity',exact=True).wait_for()
    page.set_viewport_size({'width':390,'height':844})
    page.wait_for_timeout(1200)
    ui.get_by_text('Latest signals',exact=True).scroll_into_view_if_needed()
    capture('mobile-macro')
    ui.get_by_text('Employment',exact=True).scroll_into_view_if_needed()
    capture('mobile-chart')
    errors=ui.locator('[data-testid="stException"]').all_text_contents()
    (OUT/'checks.json').write_text(json.dumps({'url':url,'source_commit':os.environ.get('GITHUB_SHA'),'history_selection':'Since 2018','history_changed':True,'retail_navigation':True,'exceptions':errors},indent=2))
    assert not errors,errors
    browser.close()

