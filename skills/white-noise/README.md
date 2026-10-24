# white-noise スキル

「アレクサ、ホワイトノイズを開いて」で即再生し、2時間で自動終了するプライベート用スキル。公開せず「開発中」ステージのまま使用します。

## 仕様
- 起動（LaunchRequest / PlayIntent）：追加対話なしで AudioPlayer.Play
- ループ再生：PlaybackNearlyFinished で同じ音源を ENQUEUE
- 2時間（`MAX_DURATION_SEC`、既定7200秒）経過で ENQUEUE を止め終了
- 「止めて」「キャンセル」「一時停止」：AudioPlayer.Stop
- 「再開」：先頭から再生（開始時刻はリセット）

## 環境変数（Lambda）
| 名前 | 内容 |
|---|---|
| `AUDIO_URL` | HTTPS の音源URL（S3等、例：`https://example-bucket.s3.amazonaws.com/white-noise.mp3`） |
| `MAX_DURATION_SEC` | 再生上限秒（既定 7200） |

開始時刻は再生トークンに埋め込むため、DBは不要です。

## デプロイ概要
1. Amazon 開発者アカウントを登録（本人）
2. ASK CLI または開発者コンソールでスキル作成、`skill.json` と `interactionModels/custom/ja-JP.json` を反映
3. `lambda/` を Python 3.12 で Lambda にデプロイ（`pip install -r requirements.txt -t .` して zip）
4. Lambda のトリガーに Alexa Skills Kit（スキルID検証あり）を設定し、ARN を `skill.json` に記入
5. 音源（数分のループ素材）をS3に置きHTTPSで取得可能にする
6. シミュレータ→実機で確認。公開申請はしない

※ ARN・スキルID・鍵などはコミットしないこと。
