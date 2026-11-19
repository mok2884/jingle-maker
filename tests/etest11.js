const { _electron: electron } = require('playwright-core');
(async () => {
  const app = await electron.launch({ executablePath: __dirname + '/dist/linux-unpacked/jinglemaker', args: ['--no-sandbox','--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--use-file-for-fake-audio-capture=/home/claude/apptest/rec_s16.wav'] });
  const pg = await app.firstWindow(); const errs = []; pg.on('pageerror', e => errs.push(String(e)));
  await pg.waitForFunction(() => typeof startRec === 'function' && NI); await pg.waitForTimeout(1500);
  const st = () => pg.evaluate(() => ({ mic: !!mic.stream, mon: mon.on, rec: rec.on, recCls: $('btnRec').className, recTxt: $('btnRec').textContent, monTxt: $('btnMon').textContent }));
  console.log('start', JSON.stringify(await st()));
  await pg.click('#btnRec'); await pg.waitForTimeout(200); console.log('REC while idle -> toast:', await pg.evaluate(() => $('toast').textContent));
  await pg.click('#btnMon'); await pg.waitForTimeout(1500); console.log('after monitor', JSON.stringify(await st()), 'needle', await pg.evaluate(() => vu.y.toFixed(4)));
  await pg.screenshot({ path: '/home/claude/apptest/m3.png', clip: { x: 900, y: 0, width: 655, height: 140 } });
  await pg.click('#btnRec'); await pg.waitForTimeout(3000); console.log('recording', JSON.stringify(await st()));
  await pg.click('#btnMon'); await pg.waitForTimeout(200); console.log('monitor during REC -> toast:', await pg.evaluate(() => $('toast').textContent), 'mic still', await pg.evaluate(() => !!mic.stream));
  await pg.evaluate(() => { window.confirmBox = async () => true; }); await pg.click('#btnRec'); await pg.waitForTimeout(800);
  console.log('after stop', JSON.stringify(await st()));
  await pg.click('#btnMon'); await pg.waitForTimeout(300); console.log('monitor off', JSON.stringify(await st()));
  console.log('ERR', errs); await app.close();
})().catch(e => { console.error('FAIL', e); process.exit(1); });
