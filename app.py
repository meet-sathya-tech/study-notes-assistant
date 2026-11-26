import csv
import io
import json
import streamlit as st

import db
import rag
from auth import login_gate
from extract import read_pdf_pages
from processor import process
from prompts import STYLES, LANGUAGES

MAX_FILES = 5
MIN_CHARS = 200

st.set_page_config(page_title="Study Notes Assistant", page_icon="📚", layout="wide")
db.init_db()
user = login_gate()            # stops here until logged in
user_id = user["id"]

# A "pending_open" request must be applied BEFORE the sidebar widget is created
if "pending_open" in st.session_state:
    st.session_state["active_doc"] = st.session_state.pop("pending_open")


def cards_to_anki_csv(cards) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter="\t")
    for c in cards:
        writer.writerow([c["question"], c["answer"]])
    return buf.getvalue()


# ---------- Sidebar: account and saved documents ----------
docs = db.list_documents(user_id)
active_id = None
with st.sidebar:
    st.markdown(f"👤 **{user['username']}**")
    if st.button("Log out"):
        st.session_state.clear()
        st.rerun()
    st.divider()
    st.subheader("📂 My documents")
    if docs:
        ids = [d["id"] for d in docs]
        labels = {d["id"]: f"{d['name']} ({d['created_at'][:10]})" for d in docs}
        if st.session_state.get("active_doc") not in ids:
            st.session_state["active_doc"] = ids[0]
        active_id = st.selectbox("Open a saved document", ids,
                                 format_func=lambda i: labels[i], key="active_doc")
        if st.button("🗑️ Delete this document"):
            db.delete_document(user_id, active_id)
            rag.delete_index(user_id, active_id)
            st.rerun()
    else:
        st.info("No documents yet. Add one in the 'New document' tab.")

# ---------- Main area ----------
st.title("📚 Study Notes Assistant")
if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))

doc = db.get_document(user_id, active_id) if active_id else None
tab_new, tab_study, tab_chat = st.tabs(["➕ New document", "📖 Study", "💬 Chat with notes"])

# ===== Tab 1: add a document =====
with tab_new:
    mode = st.radio("Input type", ["Upload PDFs", "Paste text"], horizontal=True)
    incoming = {}                     # name -> [(page, text), ...]

    if mode == "Upload PDFs":
        files = st.file_uploader("Choose one or more PDFs", type="pdf",
                                 accept_multiple_files=True)
        if len(files) > MAX_FILES:
            st.warning(f"Only the first {MAX_FILES} files will be used.")
            files = files[:MAX_FILES]
        for f in files:
            try:
                pages = read_pdf_pages(f)
            except Exception:
                st.warning(f"Could not read '{f.name}'. Skipping it.")
                continue
            if sum(len(t) for _, t in pages) < MIN_CHARS:
                st.warning(f"'{f.name}' has too little text (maybe scanned). Skipping it.")
                continue
            incoming[f.name] = pages
    else:
        title = st.text_input("Title", value="My notes")
        pasted = st.text_area("Paste your notes here", height=250)
        if len(pasted.strip()) >= MIN_CHARS:
            incoming[title.strip() or "My notes"] = [(1, pasted)]

    c1, c2 = st.columns(2)
    style = c1.selectbox("Summary style", list(STYLES.keys()))
    language = c2.selectbox("Output language", LANGUAGES)
    num_cards = st.slider("Number of flashcards", 5, 20, 10)
    with_quiz = st.checkbox("Include a quiz (1 extra API call per document)", value=True)

    if st.button("Generate and save", type="primary"):
        if not incoming:
            st.error("Please add a readable PDF or paste enough text.")
        else:
            progress = st.progress(0.0, text="Starting...")
            last_id, failed = None, False
            try:
                for i, (name, pages) in enumerate(incoming.items()):
                    progress.progress(i / len(incoming), text=f"Processing: {name}")
                    text = "\n".join(t for _, t in pages)
                    results = process(text, num_cards, style, language, with_quiz)
                    last_id = db.add_document(user_id, name, pages, results)
                    progress.progress((i + 0.5) / len(incoming),
                                      text=f"Indexing for chat: {name}")
                    rag.index_document(user_id, last_id, pages)
                progress.progress(1.0, text="Done!")
            except Exception as e:
                failed = True
                progress.empty()
                st.error(f"Something went wrong: {e}")
            if last_id and not failed:
                st.session_state["pending_open"] = last_id
                st.session_state["flash"] = "Saved! Open the Study or Chat tab."
                st.rerun()

# ===== Tab 2: study material =====
with tab_study:
    if not doc:
        st.info("Add a document, or pick one from the sidebar.")
    else:
        res = json.loads(doc["results_json"])
        st.subheader(doc["name"])
        if res["cards"]:
            st.download_button("⬇️ Download flashcards (Anki CSV)",
                               cards_to_anki_csv(res["cards"]),
                               file_name=f"{doc['name']}_anki.csv", mime="text/csv",
                               key=f"anki_{doc['id']}")

        t1, t2, t3, t4 = st.tabs(["Summary", "Key Points", "Flashcards", "Quiz"])
        with t1:
            st.write(res["summary"])
        with t2:
            st.markdown(res["points"])
        with t3:
            if not res["cards"]:
                st.warning("No flashcards were created for this document.")
            for i, c in enumerate(res["cards"], 1):
                with st.expander(f"Q{i}. {c['question']}"):
                    st.write(c["answer"])
        with t4:
            quiz = res["quiz"]
            if not quiz:
                st.info("This document has no quiz.")
            else:
                with st.form(key=f"quiz_form_{doc['id']}"):
                    for i, q in enumerate(quiz):
                        st.radio(f"Q{i+1}. {q['question']}", q["options"],
                                 index=None, key=f"quiz_{doc['id']}_{i}")
                    submitted = st.form_submit_button("Check my score")
                if submitted:
                    score = 0
                    for i, q in enumerate(quiz):
                        picked = st.session_state.get(f"quiz_{doc['id']}_{i}")
                        correct = q["options"][q["answer_index"]]
                        if picked == correct:
                            score += 1
                            st.success(f"Q{i+1}: Correct")
                        else:
                            st.error(f"Q{i+1}: Wrong. Correct answer: {correct}")
                        if q["explanation"]:
                            st.caption(q["explanation"])
                    st.subheader(f"Score: {score} / {len(quiz)}")

# ===== Tab 3: chat with the document =====
with tab_chat:
    if not doc:
        st.info("Add a document, or pick one from the sidebar.")
    else:
        st.caption(f"Asking questions about: **{doc['name']}**")
        pages = json.loads(doc["pages_json"])
        rag.ensure_indexed(user_id, doc["id"], pages)

        for m in db.get_messages(doc["id"]):
            with st.chat_message(m["role"]):
                st.markdown(m["content"])

        question = st.chat_input("Ask a question about this document",
                                 key=f"chat_{doc['id']}")
        if question:
            with st.chat_message("user"):
                st.markdown(question)
            db.add_message(doc["id"], "user", question)

            with st.chat_message("assistant"):
                with st.spinner("Searching your notes..."):
                    try:
                        reply, hits = rag.answer(user_id, doc["id"], question)
                    except Exception as e:
                        reply, hits = f"Something went wrong: {e}", []
                used = sorted({h["page"] for h in hits})
                if used:
                    reply += f"\n\n*Sources: pages {', '.join(map(str, used))}*"
                st.markdown(reply)
                if hits:
                    with st.expander("Show retrieved passages"):
                        for h in hits:
                            st.markdown(f"**Page {h['page']}**")
                            st.caption(" ".join(h["text"].split()))
            db.add_message(doc["id"], "assistant", reply)