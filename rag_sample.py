#!/usr/bin/env python
"""
Minimal yet pedagogical Retrieval-Augmented Generation (RAG) sample.

Usage:
    # 1) Ingest documents
    python rag_sample.py ingest --docs_dir path/to/docs --persist_dir .chroma

    # 2) Ask questions
    python rag_sample.py ask "質問本文" --persist_dir .chroma
"""
import argparse
from dotenv import load_dotenv
import os
import sys
from pathlib import Path
from typing import List

# -------- LangChain / Chroma imports --------
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain.prompts import PromptTemplate
from langchain.schema import Document

# -------- Logging utility --------
def log(step: str):
    print(f"[RAG] {step}")

# -------- Common constants --------
EMBED_MODEL_NAME = "text-embedding-3-small"   # 1 token ≒ 1 char, 16k ctx
CHAT_MODEL_NAME  = "gpt-4o-mini"              # 好みで変更
CHUNK_SIZE       = 400                        # token 相当
CHUNK_OVERLAP    = 40                         # 次チャンクと重なり

# ===== Ingestion phase =====
def ingest_documents(docs_dir: Path, persist_dir: Path):
    """
    1. docs_dir 配下の .txt/.md/.rst を読み込む
    2. 400字前後でチャンク化
    3. OpenAI Embedding → Chroma に格納
    """
    log(f"Start ingestion from: {docs_dir}")

    # 1) ロード（拡張子フィルタ）
    file_paths = list(docs_dir.rglob("*.[tm][dx][t]"))  # *.txt, *.md
    if not file_paths:
        log("No text/markdown files found. Abort.")
        sys.exit(1)

    raw_docs: List[Document] = []
    for fp in file_paths:
        loader = TextLoader(str(fp), encoding="utf-8")
        raw_docs.extend(loader.load())
    log(f"Loaded {len(raw_docs)} document(s).")

    # 2) チャンク化
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        add_start_index=True,
    )
    chunks = splitter.split_documents(raw_docs)
    log(f"Split into {len(chunks)} chunk(s). "
        f"(size≈{CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")

    # 3) Embedding + ベクトルDB保存
    embeddings = OpenAIEmbeddings(model=EMBED_MODEL_NAME)
    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(persist_dir),
        collection_name="umamusume-rag",
    )
    log(f"Persist dir: {persist_dir}  (saved {vectordb._collection.count()} vectors)")

# ===== Query phase =====
def answer_question(question: str, persist_dir: Path, k: int = 5):
    """
    1. 質問をベクトル化
    2. Top-k 類似チャンク取得
    3. チャンク＋質問をプロンプトとして LLM へ
    4. Grounded 生成文を出力
    """
    log("Load vector store")
    embeddings = OpenAIEmbeddings(model=EMBED_MODEL_NAME)
    vectordb = Chroma(
        persist_directory=str(persist_dir),
        embedding_function=embeddings,
        collection_name="umamusume-rag",
    )

    log(f"Retrieve top-{k} relevant chunks")
    relevant_docs = vectordb.similarity_search(question, k=k)

    # --- プロンプト組み立て ---
    context = "\n\n".join([d.page_content for d in relevant_docs])
    template = """あなたはウマ娘Pretty Derbyの専門家です。
以下は参考情報です。必要に応じて引用しつつ、質問に日本語で答えてください。
===参考情報===
{context}
===質問===
{question}
===回答===
"""
    prompt = PromptTemplate(
        template=template,
        input_variables=["context", "question"],
    ).format(context=context, question=question)

    #log(f"Input LLM context{context}, question={question}")
    log("Call LLM (chat completion)")
    chat = ChatOpenAI(model_name=CHAT_MODEL_NAME, temperature=0.2)
    response = chat.invoke(prompt)  # ← LangChain v0.2 API

    print("\n====== ⬇︎ ASSISTANT ANSWER ⬇︎ ======\n")
    print(response.content)
    print("\n====== ⬆︎  END OF ANSWER  ⬆︎ ======\n")

# ===== CLI entrypoint =====
def main():
    parser = argparse.ArgumentParser(description="Simple RAG sample")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest_p = sub.add_parser("ingest", help="Embed & store docs")
    ingest_p.add_argument("--docs_dir", type=Path, required=True,
                          help="Directory containing source text")
    ingest_p.add_argument("--persist_dir", type=Path, default=Path(".chroma"),
                          help="Where to persist Chroma DB")

    ask_p = sub.add_parser("ask", help="Ask a question")
    ask_p.add_argument("question", type=str)
    ask_p.add_argument("--persist_dir", type=Path, default=Path(".chroma"))
    ask_p.add_argument("-k", type=int, default=5, help="retriever top-k")

    args = parser.parse_args()

    if args.command == "ingest":
        ingest_documents(args.docs_dir, args.persist_dir)
    elif args.command == "ask":
        answer_question(args.question, args.persist_dir, k=args.k)
    else:
        parser.print_help()

if __name__ == "__main__":
    load_dotenv()
    if "OPENAI_API_KEY" not in os.environ:
        print("ERROR: OPENAI_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    main()
