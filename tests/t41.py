import asyncio, json
from playwright.async_api import async_playwright
STUB = """
(() => {
  const P = FileSystemHandle.prototype;
  P.queryPermission = async () => 'granted'; P.requestPermission = async () => 'granted';
  navigator.storage.getDirectory().then(r => r.getDirectoryHandle('作業', { create: true })).then(h => window.__opfs = h);
  const put = IDBObjectStore.prototype.put;
  IDBObjectStore.prototype.put = function (v, k) { if (v instanceof FileSystemHandle) v = { __opfs: v.name }; return put.call(this, v, k); };
  const rg = Object.getOwnPropertyDescriptor(IDBRequest.prototype, 'result').get;
  Object.defineProperty(IDBRequest.prototype, 'result', { get() { const r = rg.call(this); return (r && r.__opfs) ? window.__opfs : r; } });
  window.showDirectoryPicker = async () => { const r = await navigator.storage.getDirectory(); return await r.getDirectoryHandle('作業', { create: true }); };
})();
"""
async def opfs_list(pg, path):
  return await pg.evaluate("""async (path) => { let d = await navigator.storage.getDirectory(); d = await d.getDirectoryHandle('作業'); for (const p of path) d = await d.getDirectoryHandle(p); const out = []; for await (const [n, h] of d.entries()) out.push(n + (h.kind === 'directory' ? '/' : '')); return out.sort(); }""", path)
async def main():
  async with async_playwright() as p:
    b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--use-file-for-fake-audio-capture=/home/claude/apptest/rec_s16.wav','--autoplay-policy=no-user-gesture-required'])
    ctx = await b.new_context(viewport={'width':1600,'height':900}); await ctx.add_init_script(STUB)
    pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg._dlg = lambda d: asyncio.ensure_future(d.accept()); pg.on('dialog', pg._dlg)
    await pg.goto('http://localhost:8765/jingle-maker.html'); await pg.wait_for_timeout(800)
    # clean OPFS, pre-place backing tracks
    await pg.evaluate("""async () => { const r = await navigator.storage.getDirectory(); try { await r.removeEntry('作業', { recursive: true }); } catch (e) {} const d = await (await r.getDirectoryHandle('作業', { create: true })).getDirectoryHandle('ジングルオケ', { create: true });
      for (const n of ['sample_oke_14bars_034.2s_-12dB.wav','sample_oke_10bars_024.6s_-12dB.wav','sample_oke_18bars_043.8s_-12dB.wav']) { const ab = await (await fetch('/oke/' + n)).arrayBuffer(); const w = await (await d.getFileHandle(n, { create: true })).createWritable(); await w.write(ab); await w.close(); } }""")
    print('dialog text:', (await pg.inner_text('.modalBack .dmsg'))[:40])
    await pg.click('.modalBack button[data-a="pick"]'); await pg.wait_for_timeout(1500)
    print('root after pick:', await opfs_list(pg, []), '| oke:', await pg.evaluate("()=>bgm.list.length"), '| status:', await pg.evaluate("()=>$('statusBar').innerText.split('\\n')[0]"))
    # load WAV -> session folder + auto-save right away
    await pg.set_input_files('#fileWav', '/home/claude/apptest/rec16.wav'); await pg.wait_for_timeout(3000)
    sname = await pg.evaluate("()=>sess.dir && sess.dir.name"); print('session folder:', sname, await opfs_list(pg, ['セッション', sname]), 'jm_open', await pg.evaluate("()=>localStorage.getItem('jm_open')"))
    await pg.evaluate("()=>{ addMark(45*48000); addMark(70*48000); }"); await pg.wait_for_timeout(300)
    await pg.click('.take .noEd'); await pg.fill('.take .fname', 'test1'); await pg.click('.take .mk')
    await pg.wait_for_function("()=>takes[0].made", timeout=60000); await pg.wait_for_timeout(500)
    print('jingle folder:', await opfs_list(pg, ['セッション', sname, 'ジングル']))
    # top lane ctrl+dblclick + 全体
    cv = await pg.query_selector('#topCanvas'); bb = await cv.bounding_box()
    await pg.keyboard.down('Control'); await pg.mouse.move(bb['x']+bb['width']*0.3, bb['y']+50); await pg.mouse.down(); await pg.mouse.up(); await pg.mouse.down(click_count=2); await pg.mouse.up(click_count=2); await pg.keyboard.up('Control')
    print('top zoom view', await pg.evaluate("()=>[topL.fit, topL.view && ((topL.view.v1-topL.view.v0)/48000).toFixed(2), (topL.cursor/48000).toFixed(2)]"), 'marks', await pg.evaluate("()=>marks.length"))
    await pg.click('#topFit'); print('after 全体 fit', await pg.evaluate("()=>topL.fit"))
    # live x1.4 switching
    await pg.evaluate("()=>{ setActive(takes[0]); takes[0].cursor=48000*5; takes[0].cursorMoved=true; togglePlay(true); }"); await pg.wait_for_timeout(1000)
    p1 = await pg.evaluate("()=>Player.pos()/48000"); await pg.click('.take .spdb'); await pg.wait_for_timeout(1000)
    p2 = await pg.evaluate("()=>[Player.src?1:0, Player.pos()/48000, !!(Player.src&&Player.src.fast)]"); await pg.click('.take .spdb'); await pg.wait_for_timeout(500)
    p3 = await pg.evaluate("()=>[Player.src?1:0, Player.pos()/48000, !!(Player.src&&Player.src.fast)]"); await pg.evaluate("()=>Player.stop()")
    print('x1.4 live: before %.2f, after toggle on %s, after toggle off %s' % (p1, p2, p3))
    # second tab is blocked
    pg2 = await ctx.new_page(); await pg2.goto('http://localhost:8765/jingle-maker.html'); await pg2.wait_for_timeout(1200)
    print('second tab blocked:', await pg2.evaluate("()=>!!document.getElementById('tabBlock')")); await pg2.close()
    # accidental reload -> resume
    dl=[]
    pg.remove_listener('dialog', pg._dlg); pg.on('dialog', lambda d: (dl.append(d.type), asyncio.ensure_future(d.accept())))
    await pg.evaluate("()=>{ window.__x=1 }")
    await pg.close(run_before_unload=True); await asyncio.sleep(1.5)
    print('beforeunload dialogs:', dl, 'closed', pg.is_closed())
    pg = await ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('crash', lambda *a: print('CRASH')); pg.on('close', lambda *a: print('CLOSE'))
    pg.on('console', lambda m: print('console:', m.text) if m.type=='error' else None)
    pg.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
    await pg.goto('http://localhost:8765/jingle-maker.html'); await asyncio.sleep(1.5)
    print('after reload dialog:', (await pg.inner_text('.modalBack .dmsg'))[:30])
    await pg.click('.modalBack button[data-a="use"]'); await pg.wait_for_timeout(1500)
    print('resume prompt:', (await pg.inner_text('.modalBack .dmsg'))[:50])
    await pg.click('.modalBack .drow button.primary'); await pg.wait_for_timeout(3000)
    print('restored:', await pg.evaluate("()=>({len:(M.len/48000).toFixed(1), takes:takes.length, start:takes[0].start&&(takes[0].start/48000).toFixed(2), made:takes[0].made&&takes[0].made.file, sess:sess.name})"))
    # gap warnings: 3 ms -> log only, 10 ms -> alarm + marker
    await pg.click('#btnMon'); await pg.wait_for_timeout(1200); await pg.click('#btnRec'); await pg.wait_for_timeout(4000)
    await pg.evaluate("()=>{ captureGap(144, 3, {pos: 192000, drift: 0.0030, ref: 0, sr: 48000}); captureGap(480, 3, {pos: 200000, drift: 0.0130, ref: 0.003, sr: 48000}); }"); await pg.wait_for_timeout(300)
    print('alarm:', await pg.evaluate("()=>$('recAlarm').hidden?'':$('recAlarm').innerText"))
    await pg.evaluate("()=>{ window.confirmBox = async () => true; }"); await pg.click('#btnRec'); await pg.wait_for_timeout(1500)
    log = await pg.evaluate("async()=>{ try { return await (await (await sess.dir.getFileHandle('_ログ.txt')).getFile()).text(); } catch(e) { return 'none'; } }")
    print('LOG:\n' + log)
    print('gap marker stored:', await pg.evaluate("()=>sess.recs.map(r=>r.gaps||[])"))
    await pg.screenshot(path='/home/claude/apptest/v140.png')
    print('errors', errs); await b.close()
asyncio.run(main())
