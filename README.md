# ジングルメーカー（JingleMaker）

ナレーションを録音（または WAV を読み込み）して、区切って、言い直しを詰めて、スタートを打って Done で、オケを乗せた完パケ WAV を作るツール。

- 本体は `index.html` の1枚だけ（HTML ＋ JavaScript。外部のライブラリやサーバーは使わない）
- Chrome か Edge で開く。作業フォルダを選ぶと、中に `セッション\` と `ジングルオケ\` ができる。完パケは各セッションの `ジングル\` に入る
- オケ（バックの音源）はこのリポジトリには入っていない。`ジングルオケ\` に長さ違いの WAV を自分で入れる

## フォルダ

| 場所 | 中身 |
|---|---|
| `index.html` | アプリ本体（GitHub Pages でもこれが開く） |
| `exe/` | Electron で包んだ exe 版を作るためのファイル。中身は `index.html` と同じ |
| `tools/mkzip.py` | exe 版の配布 zip を作る |
| `tests/` | 動作確認のスクリプト（試験用の音声ファイルは入っていない） |

## exe 版の作り方

```
cp index.html exe/app/index.html
cd exe
npm install
npx electron-builder --win portable --x64      # dist/JingleMaker.exe
python3 ../tools/mkzip.py <版>                  # JingleMaker_v<版>.zip
```

コード署名はしていない。Windows 11 の「スマート アプリ コントロール」が有効な PC では exe が止められるので、その場合は HTML 版を使う。
