# my-azon-homeai-skil

Alexa 自作スキルと、家族のテレビ視聴を簡単にする定型アクション（ルーティン）の計画・雛形リポジトリです。

状態：**計画のみ（未着手）**

## 目的
1. **計画A**：ホワイトノイズを2時間再生するだけの自作スキルを、公開せず自分のデバイスだけで使う。
2. **計画B**：80歳の家族のリビング（Fire TV Cube＋TCL製テレビ）で、簡単な呼びかけでプライムビデオ／YouTubeの特定番組をすぐ視聴できるようにする。

## 概要
- 計画A：ASKカスタムスキル＋AudioPlayer＋AWS Lambda (Python)。音源はS3。開発中ステージのまま使用。
- 計画B：スキルではなく Alexa 定型アクションで実現（プライム/YouTubeを操作する公開APIがないため）。

## ディレクトリ構成
```
docs/plan.md                 計画の整理版
docs/routines-checklist.md   計画B 実機検証チェックリスト
skills/white-noise/          計画A スキル雛形
  skill.json
  interactionModels/custom/ja-JP.json
  lambda/lambda_function.py
  lambda/requirements.txt
```

## 次のステップ
- **ブロッカー：Amazon 開発者アカウントの登録（アカウント所有者本人が実施）**
- その後：スキル＋Lambda作成 → 音源をS3へ → シミュレータ/実機で確認
- 計画B：YouTubeチャンネル名の特定、定型アクションの実機検証

## 注意
認証情報・鍵・個人情報はこのリポジトリに一切含めません。音源URL等は環境変数で設定します。
