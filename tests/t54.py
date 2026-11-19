import asyncio
from playwright.async_api import async_playwright
STUB=open('t41.py').read().split('STUB = """')[1].split('"""')[0]
async def main():
  async with async_playwright() as p:
    b = await p.chromium.launch(executable_path='/usr/bin/google-chrome')
    ctx = await b.new_context(viewport={'width':1700,'height':1000}); await ctx.add_init_script(STUB)
    pg = await ctx.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('http://localhost:8765/jingle-maker.html'); await asyncio.sleep(1)
    await pg.click('.modalBack button[data-a="pick"]'); await asyncio.sleep(1)
    await pg.set_input_files('#fileWav', 'prod.wav'); await asyncio.sleep(4)
    await pg.evaluate("()=>{ [47,100].forEach(t=>addMark(t*48000)); }"); await asyncio.sleep(1)
    # top lane menu
    cv = await pg.query_selector('#topCanvas'); bb = await cv.bounding_box()
    await pg.evaluate("()=>{ topL.sel=[30*48000,40*48000]; topDirty=true; }"); await asyncio.sleep(0.2)
    xs = bb['x'] + bb['width']*35/253.5
    await pg.mouse.click(xs, bb['y']+50, button='right'); await asyncio.sleep(0.3)
    m = await pg.query_selector('.menu'); await m.screenshot(path='menu_top.png')
    print('top menu', await pg.evaluate("()=>[...document.querySelectorAll('.menu button')].map(b=>b.innerText.replace(/\\n/g,' '))"))
    await pg.keyboard.press('Escape'); await pg.mouse.click(5,5)
    # take menu
    await pg.evaluate("()=>{ const T=takes[1]; setActive(T); T.sel=[10*48000,15*48000]; T.dirty=true; }"); await asyncio.sleep(0.3)
    tc = await pg.query_selector_all('.take canvas'); tb = await tc[1].bounding_box()
    await pg.evaluate("()=>{ const T=takes[1]; window._x=(12.5*48000-T.view.v0)/(T.view.v1-T.view.v0); }")
    fx = await pg.evaluate("()=>_x")
    await pg.mouse.click(tb['x']+tb['width']*fx, tb['y']+60, button='right'); await asyncio.sleep(0.3)
    m = await pg.query_selector('.menu'); await m.screenshot(path='menu_take.png')
    print('take menu', await pg.evaluate("()=>[...document.querySelectorAll('.menu button')].map(b=>b.innerText.replace(/\\n/g,' '))"))
    print('errors', errs); await b.close()
asyncio.run(main())
