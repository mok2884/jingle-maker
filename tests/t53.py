import asyncio, json
from playwright.async_api import async_playwright
STUB=open('t41.py').read().split('STUB = """')[1].split('"""')[0]
async def main():
  async with async_playwright() as p:
    b = await p.chromium.launch(executable_path='/usr/bin/google-chrome')
    ctx = await b.new_context(viewport={'width':1700,'height':1000}); await ctx.add_init_script(STUB)
    pg = await ctx.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('http://localhost:8765/jingle-maker.html'); await asyncio.sleep(1)
    await pg.evaluate("async()=>{ const r=await navigator.storage.getDirectory(); try{await r.removeEntry('作業',{recursive:true})}catch(e){} await r.getDirectoryHandle('作業',{create:true}); }")
    await pg.click('.modalBack button[data-a="pick"]'); await asyncio.sleep(1)
    await pg.set_input_files('#fileWav', 'prod.wav'); await asyncio.sleep(4)
    await pg.evaluate("()=>{ [47,100,140,176,214].forEach(t=>addMark(t*48000)); }"); await asyncio.sleep(1)
    async def run(js):
      await pg.evaluate("()=>{window._candDebug=null}"); await pg.evaluate(js)
      await pg.wait_for_function("()=>window._candDebug || /見つかりません|ありません/.test($('toast').textContent)", timeout=60000)
      return await pg.evaluate("()=>[_candDebug, $('toast').textContent]")
    print('TOP  ', json.dumps(await run("()=>{ topL.sel=[233.25*48000,235.45*48000]; findCands(selRange(topL), topL); }"), ensure_ascii=False))
    # in take 2 (starts at 47 s), with START/END set around the OK take; select the first 2.3 s of the OK take
    print('TAKE2', json.dumps(await run("()=>{ const T=takes[1], o=T.segs[0][0]; T.start=69.0*48000-o; T.end=95.6*48000-o; T.sel=[69.2*48000-o, 71.5*48000-o]; findCands(selRange(T), T); }"), ensure_ascii=False))
    print('in take 2 range only:', await pg.evaluate("()=>cands.every(c=>c[0]>=47*48000 && c[1]<=100*48000)"))
    # after an edit inside the take (cut 1 s before the selection), search again: pieces in order
    print('TAKE2 after cut', json.dumps(await run("()=>{ const T=takes[1], o=T.segs[0][0]; opDelete(T, 60*48000-o, 61*48000-o); T.sel=[68.2*48000-o, 70.5*48000-o]; findCands(selRange(T), T); }"), ensure_ascii=False))
    await pg.evaluate("()=>{ setActive(takes[1]); redrawAll(); }"); await asyncio.sleep(0.4)
    el = await pg.query_selector_all('.take'); await el[1].screenshot(path='cand_take.png')
    print('errors', errs); await b.close()
asyncio.run(main())
