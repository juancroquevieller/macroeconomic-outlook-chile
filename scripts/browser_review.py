"""Real Chromium screenshots and interaction checks for visual review."""
import json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
OUT=Path('verification/browser');OUT.mkdir(parents=True,exist_ok=True)
url=os.environ.get('DASHBOARD_URL','http://127.0.0.1:8501')
with sync_playwright() as p:
    browser=p.chromium.launch()
    page=browser.new_page(viewport={'width':1440,'height':1100},device_scale_factor=1)
    page.goto(url,wait_until='domcontentloaded',timeout=90000)
    page.get_by_text('Economic activity',exact=True).wait_for(timeout=90000)
    page.locator('.js-plotly-plot').first.wait_for(timeout=60000)
    page.wait_for_timeout(2500)
    def capture(name):
        page.screenshot(path=str(OUT/(name+'.png')),full_page=True)
    capture('macro-top')
    page.get_by_text('Employment',exact=True).scroll_into_view_if_needed()
    capture('macro-bottom')
    page.get_by_label('History',exact=True).click()
    page.get_by_role('option',name='5 years',exact=True).click()
    page.wait_for_timeout(1200)
    page.get_by_text('Economic activity',exact=True).scroll_into_view_if_needed()
    capture('macro-five-years')
    page.get_by_role('radio',name='Retail outlook',exact=True).check()
    page.get_by_text('Consumer demand',exact=True).wait_for()
    page.wait_for_timeout(2000)
    page.get_by_text('Latest signals',exact=True).scroll_into_view_if_needed()
    capture('retail-top')
    page.get_by_text('Retail channels',exact=True).scroll_into_view_if_needed()
    capture('retail-bottom')
    errors=page.locator('[data-testid="stException"]').all_text_contents()
    (OUT/'checks.json').write_text(json.dumps({'url':url,'history_changed':True,'retail_navigation':True,'exceptions':errors},indent=2))
    assert not errors,errors
    browser.close()
