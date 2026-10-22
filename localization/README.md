# 日本語化とローカル確認

対象の英語版は、隣接する `ocp-dev-days-rdshw-showroom` のコミット `49ef5dd1809feb6ce7dab60140342eba9622cedb` です。英語版の作業ツリーは変更していません。

## ローカルで英語版と日本語版を比較する

Node.js 18 以降と Python 3 を使用します。以下は日本語版リポジトリのルートで実行します。

```sh
npm ci
npm run build:preview
npm run verify:preview
npm run serve:preview
```

- [日本語版](http://127.0.0.1:8080/ja/modules/index.html)
- [英語版](http://127.0.0.1:8081/en/modules/index.html)

英語版と日本語版は異なるポートで開いてください。Showroom の進捗機能はブラウザの保存領域を使うため、同じポートで両言語を開くと、再開先と進捗が混ざります。`serve:preview` は 2 つのポートを同時に起動します。終了は Ctrl+C です。すでにポートが使用中の場合は、先に既存のプレビューを停止してください。

ビルド後に本文を変更した場合は再ビルドし、ブラウザを再読み込みします。プレビューは実際の Antora と Showroom テーマを使用します。初回は npm と GitHub への接続が必要です。テーマの配布先は英語版と同じ `latest` なので、後日変更される可能性があります。検証時のハッシュは `verification.json` に記録しています。

ラボの認証情報やホスト名は仮の値です。`localization/playbook-en.yml` と `playbook-ja.yml` に同じ値を設定しています。実際のパスワードや API キーを保存しないでください。OpenShift、GitLab、MaaS、docserver への接続やラボ操作の成否は、ローカルの静的プレビューでは検証できません。

## 検証するもの

`verify:preview` は、生成済みの両版が存在することを必須とし、次を照合します。

- 英語版に対応する全 AsciiDoc ファイル、コード・コピー用ブロック、参照先。
- 英語版の画像ファイルの SHA-256 と、添付ファイル・サンプルコードの内容。
- 全公開 HTML のリンク、ページ内フラグメント、画像、添付ファイルの存在。
- 強調とインラインコードの数・内容、本文およびナビゲーションのリンク先。
- 日本語化した表示文言を含む、生成されたインライン JavaScript の構文。

原文の余分なバッククォートの修正は、該当ファイルの修正前後のコード内容を明示して例外判定します。それ以外の新しい差異は失敗として扱います。画像やリンクの検査はファイルの存在と参照先の照合であり、外部サービスが応答する保証ではありません。

実施結果は [REPORT.md](REPORT.md)、機械的な検査は `verification.json` と `script-verification.json`、ブラウザでの比較記録は `browser-verification.json` にあります。

## 次回の英語版更新時

`source-manifest.json` に英語版のコミットと全コンテンツのハッシュを保存しています。新しい英語版とのファイル差分を確認し、日本語版に反映してから、両版を再ビルド・再検証してください。検証レポートは再実行により更新されます。ブラウザの操作確認は別途必要です。

## OpenShift 起動後の確認

現在は環境が未起動のため、この段階は未実施です。`userXX-showroom` は候補であり、実際の名前と配信方式は起動後に確認します。

1. 対象クラスタへの接続、ワークショップの Route、利用するユーザーと Namespace を確認します。
2. Showroom の Deployment / StatefulSet、Pod、ConfigMap 等から、コンテンツの Git URL、ブランチ、ビルド方式、環境属性、テーマの読み込み方を確認します。日本語用 supplemental UI と転送用拡張も読み込まれることを確認します。Secret の内容はレポートに出力しません。
3. 日本語版の Git URL と検証対象のリビジョンが、Showroom から取得可能か確認します。ローカルの未コミット変更は、リモートの Showroom には自動反映されません。Git の公開が必要な構成か、検証用の一時反映が可能かを確認してから、その環境に合った方法で反映します。
4. 反映前の設定と復旧方法を記録し、対象のワークショップだけに適用します。必要な再ビルド・再起動を実施し、準備完了を確認します。
5. Route をブラウザで開き、ホーム、各モジュール、ナビゲーション、旧 module-1 URL、ページ内リンク、太字、コード、表、注釈、折りたたみ、コピー欄、図を確認します。
6. 実ユーザーのユーザー名・パスワード・ホスト名・LLM 設定の展開、Resources の値、docserver によるパスワードやルーム ID の取得を確認します。
7. OpenShift Console、Developer Hub、Dev Spaces、GitLab、Argo CD、Matrix / Rocket.Chat、HelpDesk、MaaS へのリンクを確認します。module-5 の添付 `logging.yaml` もダウンロードして照合します。
8. 実環境での実施日時、対象、反映したリビジョン、画面と操作の結果をレポートへ追記します。

参考: [Showroom コンテンツリポジトリの公式ガイド](https://rhpds.github.io/showroom_template_nookbag/modules/content-repo.html)。実際の構成を確認するまでは、この環境への具体的なデプロイコマンドを決めません。
