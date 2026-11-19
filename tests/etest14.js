const { _electron: electron } = require('playwright-core');
const fs = require('fs');
(async () => {
  const app = await electron.launch({ executablePath: __dirname + '/dist/linux-unpacked/jinglemaker', args: ['--no-sandbox','--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--use-file-for-fake-audio-capture=/home/claude/apptest/rec_s16.wav'] });
  const pg = await app.firstWindow(); const errs = []; pg.on('pageerror', e => errs.push(String(e)));
  await pg.waitForFunction(() => typeof startRec === 'function' && NI); await pg.waitForTimeout(1500);
  await pg.click('#btnMon'); await pg.waitForTimeout(1500); await pg.click('#btnRec'); await pg.waitForTimeout(6000);
  await pg.evaluate(() => mic.stream.getAudioTracks()[0].stop()); await pg.waitForTimeout(3000);
  const st = await pg.evaluate(() => ({ rec: rec.on, mon: mon.on, mic: !!mic.stream, len: (M.len / 48000).toFixed(2), btn: $('btnRec').innerText.replace(/\n/g, ' '), alarm: $('recAlarm').innerText.split('\n').slice(1).join(' / '), dir: sess.dir && sess.dir.path, recs: sess.recs.map(r => [r.file, r.done]) }));
  console.log(JSON.stringify(st, null, 1));
  const d = st.dir; console.log('session files', fs.readdirSync(d), 'rec', fs.readdirSync(d + '/録音'));
  console.log(fs.readFileSync(d + '/_ログ.txt', 'utf8'));
  console.log('recording marker gone', !fs.existsSync(d + '/_録音中.txt'), '| still recording (blocks closing)?', await pg.evaluate(() => rec.on));
  console.log('ERR', errs); await app.close();
})().catch(e => { console.error('FAIL', e); process.exit(1); });
