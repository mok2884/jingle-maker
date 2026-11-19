import asyncio
from playwright.async_api import async_playwright
STUB=open('t41.py').read().split('STUB = """')[1].split('"""')[0]
async def main():
  async with async_playwright() as p:
    b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--use-file-for-fake-audio-capture=/home/claude/apptest/rec_s16.wav','--autoplay-policy=no-user-gesture-required'])
    ctx = await b.new_context(viewport={'width':1600,'height':900}); await ctx.add_init_script(STUB)
    pg = await ctx.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('http://localhost:8765/jingle-maker.html'); await asyncio.sleep(1)
    await pg.evaluate("async()=>{ const r=await navigator.storage.getDirectory(); try{await r.removeEntry('作業',{recursive:true})}catch(e){} await r.getDirectoryHandle('作業',{create:true}); }")
    await pg.click('.modalBack button[data-a="pick"]'); await asyncio.sleep(1.5)
    await pg.click('#btnMon'); await asyncio.sleep(1.5); await pg.click('#btnRec'); await asyncio.sleep(6)
    before = await pg.evaluate("()=>M.len/48000")
    await pg.evaluate("()=>mic.stream.getAudioTracks()[0].stop()")   # same state as the USB being pulled
    await asyncio.sleep(3)
    st = await pg.evaluate("()=>({rec:rec.on, mon:mon.on, mic:!!mic.stream, len:(M.len/48000).toFixed(2), btn:$('btnRec').innerText.replace(/\\n/g,' '), mbtn:$('btnMon').innerText.replace(/\\n/g,' '), alarm:$('recAlarm').innerText, takes:takes.length, recs:sess.recs.map(r=>[r.file,r.done,(r.len/48000).toFixed(2)])})")
    print('len before pull %.2f' % before); [print(k, v) for k, v in st.items()]
    files = await pg.evaluate("async()=>{ const out=[]; for await (const [n,h] of sess.dir.entries()) out.push(n); for await (const [n] of rec.dir.entries()) out.push('rec/'+n); return out.sort(); }")
    print('files', files)
    print(await pg.evaluate("async()=>(await (await sess.dir.getFileHandle('_ログ.txt')).getFile()).text()"))
    # can record again after monitor on
    await pg.click('#btnMon'); await asyncio.sleep(1.5); await pg.click('#btnRec'); await asyncio.sleep(3); await pg.click('#btnRec'); await asyncio.sleep(1.5)
    print('again', await pg.evaluate("()=>({rec:rec.on, recs:sess.recs.map(r=>[r.file,r.done,(r.len/48000).toFixed(2)])})"))
    await pg.screenshot(path='lost.png'); print('errors', errs); await b.close()
asyncio.run(main())
