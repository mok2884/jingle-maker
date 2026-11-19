# 動作確認のスクリプト

作った人の作業環境で使っていたもの。パス（`/home/claude/...`）や試験用の音声ファイル（`rec_s16.wav`、`prod.wav` など）はこのリポジトリに入っていないので、そのままでは動かない。

- `t41.py` など（Python の Playwright ＋ ヘッドレス Chrome）：HTML 版。フォルダの選択は OPFS に差し替えて試す。偽のマイクは 16bit の WAV でないと無音になる
- `etest*.js`（Node の playwright-core の `_electron`、`xvfb-run` の上）：exe 版。`etest13.js` が通しの確認
