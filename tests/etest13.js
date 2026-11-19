// full check: layout never moves, recording is complete and saved exactly, SPLIT/END, 編集なし, Done
const { _electron: electron } = require('playwright-core');
(async () => {
  const app = await electron.launch({ executablePath: __dirname + '/dist/linux-unpacked/jinglemaker', args: ['--no-sandbox','--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--use-file-for-fake-audio-capture=/home/claude/apptest/rec_s16.wav'] });
  const pg = await app.firstWindow(); const errs = []; pg.on('pageerror', e => errs.push(String(e)));
  await pg.waitForFunction(() => typeof startRec === 'function' && NI); await pg.waitForTimeout(2500);
  const L = () => pg.evaluate(() => ['.brand','.filebtns','.topParams','#btnMark','.vu','#vuSrc','.reccol','#btnRec','#btnMon','#topCard','#topCanvas'].map(q => { const r = document.querySelector(q).getBoundingClientRect(); return q + ':' + [r.x, r.y, r.width, r.height].map(Math.round).join(','); }).join(' '));
  const states = {}; states.start = await L();
  await pg.click('#btnMon'); await pg.waitForTimeout(1500); states.monitor = await L();
  await pg.evaluate(() => { window.confirmBox = async () => true; });
  await pg.click('#btnRec'); await pg.waitForTimeout(2000); states.recording = await L();
  for (let i = 0; i < 2; i++) { await pg.waitForTimeout(8000); await pg.evaluate(() => { const s = performance.now(); while (performance.now() - s < 1000) {} }); }
  await pg.waitForFunction(() => (M.len - rec.entry.start) / 48000 > 45, null, { timeout: 120000 }); await pg.keyboard.press('m');
  await pg.waitForFunction(() => (M.len - rec.entry.start) / 48000 > 72, null, { timeout: 120000 }); await pg.keyboard.press('m');
  await pg.waitForTimeout(3000);
  const rs = await pg.evaluate(() => ({ elapsed: (performance.now() - rec.t0) / 1000, got: (M.len - rec.entry.start) / 48000, gaps: rec.entry.gaps || [], alarm: $('recAlarm').hidden ? '' : $('recAlarm').innerText }));
  await pg.click('#btnRec'); await pg.waitForTimeout(500);
  await pg.evaluate(() => rec.writeChain); await pg.waitForTimeout(1500); states.stopped = await L();
  console.log('RECORDING elapsed %.2fs, captured %.2fs, missing %d ms, gap warnings %j, alarm "%s"', rs.elapsed, rs.got, Math.round((rs.elapsed - rs.got) * 1000), rs.gaps, rs.alarm);
  // the saved WAV must hold exactly what is in memory (24-bit)
  const sv = await pg.evaluate(async () => {
    const e = sess.recs[sess.recs.length - 1], d = await recDirOf(sess.dir), f = await (await d.getFileHandle(e.file)).getFile(), ab = await f.arrayBuffer(), v = new DataView(ab);
    let o = 12, fmt = null, data = null; while (o < ab.byteLength) { const id = String.fromCharCode(...new Uint8Array(ab, o, 4)), sz = v.getUint32(o + 4, true); if (id === 'fmt ') fmt = { ch: v.getUint16(o + 10, true), sr: v.getUint32(o + 12, true), bits: v.getUint16(o + 22, true) }; if (id === 'data') { data = [o + 8, sz]; break; } o += 8 + sz + (sz & 1); }
    const n = data[1] / 3; let maxd = 0;
    for (let i = 0; i < n; i++) { const p = data[0] + i * 3; let s = v.getUint8(p) | (v.getUint8(p + 1) << 8) | (v.getInt8(p + 2) << 16); const d2 = Math.abs(s / 8388608 - M.buf[e.start + i]); if (d2 > maxd) maxd = d2; }
    const chunks = []; for await (const [nm] of d.entries()) if (/^chunk_/.test(nm)) chunks.push(nm);
    return { file: e.file, path: d.path + '/' + e.file, fmt, samples: n, memSamples: e.len, maxDiffLSB: maxd * 8388608, leftoverChunks: chunks.length, recMarker: await fileExists(sess.dir, '_録音中.txt') };
  });
  console.log('SAVED', JSON.stringify(sv));
  const tk = await pg.evaluate(() => takes.map(t => ({ name: t.name, len: +(tlen(t) / 48000).toFixed(2), end: t.end == null ? null : +(t.end / 48000).toFixed(2), gain: t.gain })));
  console.log('TAKES after SPLIT', JSON.stringify(tk));
  await pg.click('.take .noEd'); await pg.waitForTimeout(300);
  console.log('編集なし -> take1 start', await pg.evaluate(() => takes[0].start == null ? null : +(takes[0].start / 48000).toFixed(2)), 'gain', await pg.evaluate(() => takes[0].gain));
  await pg.evaluate(() => { setActive(takes[0]); takes[0].cursor = 48000 * 20; takes[0].cursorMoved = true; togglePlay(true); }); await pg.waitForTimeout(800);
  states.playing = await L(); console.log('VU label while playing:', await pg.evaluate(() => $('vuSrc').textContent)); await pg.evaluate(() => Player.stop());
  await pg.click('.take .pS'); await pg.waitForTimeout(300); await pg.evaluate(() => Player.stop()); await pg.click('.take .pE'); await pg.waitForTimeout(300); await pg.evaluate(() => Player.stop());
  await pg.fill('.take .fname', 'test_take1'); await pg.click('.take .mk');
  await pg.waitForFunction(() => takes[0].made, null, { timeout: 60000 });
  const dn = await pg.evaluate(async () => { const d = await exportDirExe(), f = await (await d.getFileHandle('test_take1.wav')).getFile(), ab = await f.arrayBuffer(), v = new DataView(ab); return { file: takes[0].made.file, oke: takes[0].made.variant, dur: +takes[0].made.dur.toFixed(2), lkfs: +takes[0].made.lkfs.toFixed(1), ch: v.getUint16(22, true), sr: v.getUint32(24, true), bits: v.getUint16(34, true), bytes: ab.byteLength }; });
  console.log('DONE', JSON.stringify(dn));
  await pg.click('#btnMon'); await pg.waitForTimeout(800); states.monitorOff = await L();
  const base = states.start; let same = true;
  for (const [k, v] of Object.entries(states)) if (v !== base) { same = false; console.log('LAYOUT DIFFERS in', k, '\n  start:', base, '\n  ' + k + ':', v); }
  console.log('LAYOUT same in all states (start, monitor, recording, stopped, playing, monitorOff):', same);
  console.log('ERR', errs); await app.close();
})().catch(e => { console.error('FAIL', e); process.exit(1); });
