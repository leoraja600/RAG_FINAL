import os
import requests
import streamlit as st


API = os.getenv(
    "EKI_API",
    "http://127.0.0.1:8000"
)


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="EKI-Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #FF4B2B, #FF416C);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #A0AEC0;
        margin-bottom: 2rem;
    }
    .stButton>button {
        background: linear-gradient(90deg, #FF416C 0%, #FF4B2B 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(255, 65, 108, 0.4);
    }
    .stTextArea>div>div>textarea {
        border-radius: 8px;
        border: 1px solid #2D3748;
        background-color: #1A202C;
    }
    .stTextArea>div>div>textarea:focus {
        border-color: #FF416C;
        box-shadow: 0 0 0 1px #FF416C;
    }
    .css-1d391kg {
        background-color: #171923;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🧠 EKI-Agent</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Agentic Multimodal RAG • Hybrid Retrieval • Self-Correction • Provenance</p>', unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "Enterprise Access"
    )

    role = st.selectbox(
        "User role",
        [
            "admin",
            "finance",
            "hr",
            "engineering",
            "public",
        ],
    )

    st.info(
        "Demo mode: public documents are available "
        "to all roles; department documents are "
        "available to matching roles/admin."
    )

    st.header(
        "Upload Knowledge"
    )

    uploaded = st.file_uploader(
        "PDF, PPTX, XLSX, CSV, TXT or image",
        type=[
            "pdf",
            "pptx",
            "xlsx",
            "csv",
            "txt",
            "png",
            "jpg",
            "jpeg",
            "webp",
            "bmp",
        ],
    )

    access = st.selectbox(
        "Document access",
        [
            "public",
            "finance",
            "hr",
            "engineering",
        ],
    )

    if (
        uploaded
        and st.button(
            "📥 Index document",
            use_container_width=True,
        )
    ):

        with st.spinner(
            "Parsing → extracting → "
            "embedding → indexing..."
        ):

            try:

                response = requests.post(
                    f"{API}/documents/upload",
                    files={
                        "file": (
                            uploaded.name,
                            uploaded.getvalue(),
                            uploaded.type
                            or
                            "application/octet-stream",
                        )
                    },
                    data={
                        "access_level": access
                    },
                    timeout=180,
                )

                if response.ok:

                    data = response.json()

                    st.success(
                        f"Indexed "
                        f"{data.get('chunks', 0)} "
                        f"chunks from "
                        f"{data.get('filename', uploaded.name)}"
                    )

                else:

                    st.error(
                        response.text
                    )

            except requests.RequestException as exc:

                st.error(
                    f"Backend connection failed: {exc}"
                )


# ============================================================
# QUERY
# ============================================================

st.subheader(
    "Ask the enterprise knowledge base"
)


q = st.text_area(
    "Question",
    value="What is the Financial Stability Report?",
    height=120,
    placeholder=(
        "Ask a question about the "
        "indexed enterprise documents..."
    ),
)


run = st.button(
    "🚀 Run EKI-Agent",
    type="primary",
    use_container_width=True,
)


# ============================================================
# EXECUTION
# ============================================================

if run and q.strip():

    with st.spinner(
        "Planner → Researcher → "
        "Writer → Critic → Self-correction"
    ):

        try:

            response = requests.post(
                f"{API}/query",
                json={
                    "query": q.strip(),
                    "user_role": role,
                },
                timeout=180,
            )

        except requests.RequestException as exc:

            st.error(
                f"Backend connection failed: {exc}"
            )

            st.stop()

    if not response.ok:

        st.error(
            response.text
        )

        st.stop()

    data = response.json()


    # ========================================================
    # ANSWER
    # ========================================================

    st.divider()

    st.header(
        "💬 Answer"
    )

    answer = data.get(
        "answer",
        ""
    )

    # --------------------------------------------------------
    # Protect UI from accidental object serialization
    # --------------------------------------------------------

    if isinstance(
        answer,
        dict
    ):

        answer = (
            answer.get("text")
            or
            answer.get("answer")
            or
            str(answer)
        )

    if isinstance(
        answer,
        list
    ):

        for item in answer:

            if isinstance(
                item,
                dict
            ):

                text = (
                    item.get("text")
                    or
                    item.get("content")
                    or
                    item.get("answer")
                )

                if text:
                    st.markdown(
                        str(text)
                    )

            else:

                st.markdown(
                    str(item)
                )

    else:

        st.markdown(
            str(answer)
        )


    # ========================================================
    # ANSWER VERIFICATION
    # ========================================================

    st.header(
        "🔎 Answer Verification"
    )

    critic = (
        data.get("critic")
        or {}
    )

    passed = bool(
        critic.get(
            "passed",
            critic.get(
                "sufficient",
                False,
            ),
        )
    )

    groundedness = float(
        critic.get(
            "groundedness",
            0.0,
        )
        or 0.0
    )

    relevance = float(
        critic.get(
            "relevance",
            0.0,
        )
        or 0.0
    )


    if passed:

        st.success(
            "✓ Answer passed evidence verification"
        )

    else:

        st.warning(
            "⚠ Answer needs additional evidence verification"
        )


    col1, col2 = st.columns(2)


    with col1:

        st.metric(
            "Groundedness",
            f"{groundedness:.2f}",
        )


    with col2:

        st.metric(
            "Answer relevance",
            f"{relevance:.2f}",
        )


    reason = critic.get(
        "reason"
    )

    if reason:

        st.caption(
            f"Critic: {reason}"
        )


    # ========================================================
    # SOURCES
    # ========================================================

    st.header(
        "📚 Sources"
    )

    citations = (
        data.get("citations")
        or []
    )


    if not citations:

        st.info(
            "No source citations were returned."
        )

    else:

        for index, citation in enumerate(
            citations,
            start=1,
        ):

            if not isinstance(
                citation,
                dict
            ):

                citation = {
                    "source":
                    str(citation)
                }


            source = (
                citation.get("source")
                or
                citation.get("filename")
                or
                citation.get("file_name")
                or
                "Unknown document"
            )


            page = (
                citation.get("page")
                or
                citation.get("page_number")
            )


            modality = (
                citation.get("modality")
                or
                "text"
            )


            score = citation.get(
                "score"
            )


            evidence_text = (
                citation.get("text")
                or
                citation.get("content")
                or
                ""
            )


            st.markdown(
                f"**{index}. 📄 {source}**"
            )


            meta1, meta2, meta3 = (
                st.columns(3)
            )


            with meta1:

                st.write(
                    "**Page:** "
                    +
                    (
                        str(page)
                        if page is not None
                        else
                        "Not specified"
                    )
                )


            with meta2:

                st.write(
                    f"**Modality:** "
                    f"`{modality}`"
                )


            with meta3:

                try:

                    st.write(
                        "**Retrieval score:** "
                        f"`{float(score):.3f}`"
                    )

                except Exception:

                    st.write(
                        "**Retrieval score:** —"
                    )


            # ------------------------------------------------
            # Evidence viewer
            #
            # This expander is NOT inside another expander.
            # ------------------------------------------------

            if evidence_text:

                with st.expander(
                    "View evidence",
                    expanded=False,
                ):

                    st.markdown(
                        str(evidence_text)
                    )


            if index < len(
                citations
            ):

                st.divider()


    # ========================================================
    # AGENT TRACE
    # ========================================================

    traces = (
        data.get("traces")
        or []
    )


    if traces:

        st.header(
            "🤖 Agent Trace"
        )

        # ----------------------------------------------------
        # ONLY ONE EXPANDER
        #
        # Nothing inside this block creates another expander.
        # ----------------------------------------------------

        with st.expander(
            "Show agent execution details",
            expanded=False,
        ):

            for index, trace in enumerate(
                traces,
                start=1,
            ):

                if not isinstance(
                    trace,
                    dict
                ):

                    st.write(
                        str(trace)
                    )

                    continue


                agent = trace.get(
                    "agent",
                    "Unknown agent"
                )

                action = trace.get(
                    "action",
                    ""
                )

                output = trace.get(
                    "output_summary",
                    ""
                )


                st.markdown(
                    f"**{index}. "
                    f"{agent} — {action}**"
                )


                if output:

                    st.code(
                        str(output),
                        language="text",
                    )


    # ========================================================
    # ITERATIONS
    # ========================================================

    iterations = data.get(
        "iterations"
    )


    if iterations is not None:

        st.caption(
            f"Retrieval iterations: "
            f"{iterations}"
        )