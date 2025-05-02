
# RAG Quick Start on AWS EC2

このリポジトリは **Retrieval‑Augmented Generation (RAG)** を Amazon Linux 2023 (ARM64) + Python + LangChain + Chroma で体験する最小構成デモです。

---

## 1. 事前準備

| 手順 | コマンド (EC2 内) |
|------|------------------|
| **① システム更新** | `sudo dnf update -y` |
| **② Python venv** | `python3 -m venv ~/ragenv && source ~/ragenv/bin/activate` |
| **③ パッケージ** | `pip install -U langchain-core langchain-openai langchain-community langchain-chroma chromadb python-dotenv` |
| **④ API キー** | `echo "OPENAI_API_KEY=sk-xxxxxxxx" > .env` |

---

## 2. ドキュメントを用意する

```bash
mkdir -p docs
cat > docs/mayano.txt   <<'EOF'
マヤノトップガンの勝負服はスカイブルーで、胸と袖に白いラインが入っている。
EOF
cat > docs/spechan.txt  <<'EOF'
スペシャルウィークの誕生日は5月2日。好きな食べ物はニンジンハンバーグ。
EOF
cat > docs/mcqueen.txt  <<'EOF'
メジロマックイーンは長距離レースが得意で、スタミナに優れる。
EOF
cat > docs/teiou.txt    <<'EOF'
トウカイテイオーは明るく前向きな性格で、跳ねるような走りが特徴。
EOF
cat > docs/suzuka.txt   <<'EOF'
サイレンススズカは大逃げ戦法でハイペースのまま先頭を譲らない。
EOF
```

---

## 3. 埋め込み (Ingest)

```bash
python rag_sample.py ingest --docs_dir docs
```

---

## 4. 質問してみる (Ask)

| # | 質問例 | 実行コマンド |
|---|--------|--------------|
| 1 | マヤノトップガンの勝負服は何色？ | `python rag_sample.py ask "マヤノトップガンの勝負服は何色？"` |
| 2 | スペシャルウィークの誕生日は？ | `python rag_sample.py ask "スペシャルウィークの誕生日は？"` |
| 3 | メジロマックイーンが得意な距離は？ | `python rag_sample.py ask "メジロマックイーンが得意な距離は？"` |
| 4 | トウカイテイオーの性格は？ | `python rag_sample.py ask "トウカイテイオーの性格は？"` |
| 5 | サイレンススズカのレース戦法は？ | `python rag_sample.py ask "サイレンススズカの戦法は？"` |

### 出力例 (抜粋)

```
====== ⬇︎ ASSISTANT ANSWER ⬇︎ ======

マヤノトップガンの勝負服はスカイブルーに白いラインが入っています。

====== ⬆︎  END OF ANSWER  ⬆︎ ======
```

---

## 5. 想定外の質問への応答

ドキュメントに含まれない質問をすると、ベクトル検索で関連チャンクが無いため次のような応答になります。

```bash
python rag_sample.py ask "ダイワスカーレットの好きな食べ物は？"
```

例:

```
申し訳ありませんが、手元の情報にはダイワスカーレットの好きな食べ物がありません。
```

---

## 6. 後片付け

```bash
deactivate                 # venv を抜ける
exit                       # EC2 からログアウト
# AWS コンソール → インスタンスを Stop / Terminate
```

---

## 付録 : トラブルシューティング

| 症状 | 対処 |
|------|------|
| `LangChainDeprecationWarning` | `from langchain_chroma import Chroma` に修正 |
| `Unauthorized` (OpenAI) | `.env` の API キーを再確認 |
| `n_results = 0` | docs に該当文章が無い → 文書を追加して `ingest` |

---

Happy RAG Hacking! 🎉
