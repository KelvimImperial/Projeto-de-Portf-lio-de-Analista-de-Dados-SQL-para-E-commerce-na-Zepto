

import os
import streamlit as st
from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit

load_dotenv()


st.set_page_config(
    page_title="Agente SQL • Chat com seu Banco de Dados",
    page_icon="🗄️",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
        .main .block-container {
            padding-top: 2rem;
            max-width: 900px;
        }
        .app-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.2rem;
        }
        .app-header h1 {
            font-size: 1.9rem;
            margin: 0;
        }
        .app-subtitle {
            color: #8a8f98;
            font-size: 0.95rem;
            margin-bottom: 1.5rem;
        }
        .status-pill {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .status-connected {
            background-color: #d1f5df;
            color: #0a7a3d;
        }
        .status-disconnected {
            background-color: #fde2e2;
            color: #b42318;
        }
        section[data-testid="stSidebar"] {
            border-right: 1px solid rgba(150,150,150,0.15);
        }
        div[data-testid="stChatMessage"] {
            border-radius: 12px;
        }
        .stExpander {
            border-radius: 10px !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent" not in st.session_state:
    st.session_state.agent = None
if "db" not in st.session_state:
    st.session_state.db = None
if "connected" not in st.session_state:
    st.session_state.connected = False



def build_agent(username, password, host, port, database, openai_model, openai_key):
    """Cria a conexão com o banco e o agente LangChain."""
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key

    db_uri = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"
    db = SQLDatabase.from_uri(db_uri)

    model = init_chat_model(openai_model, model_provider="openai")

    toolkit = SQLDatabaseToolkit(db=db, llm=model)
    tools = toolkit.get_tools()

    system_prompt = f"""
Você é um agente que responde perguntas sobre um banco de dados PostgreSQL
chamado '{database}'.

Sempre siga esta ordem:
1. Liste as tabelas disponíveis.
2. Consulte o schema da(s) tabela(s) relevante(s) antes de montar a query.
3. Escreva uma query {db.dialect} sintaticamente correta.
4. Revise a query antes de executar.
5. Execute e interprete o resultado para o usuário, em português, de forma clara.

Nunca execute comandos DML (INSERT, UPDATE, DELETE, DROP, ALTER).
Limite os resultados a no máximo 10 linhas, a menos que o usuário peça outra coisa.
"""

    agent = create_agent(model=model, tools=tools, system_prompt=system_prompt)
    return db, agent


def run_agent(agent, user_input):
    """Executa o agente passo a passo, retornando (resposta_final, passos)."""
    steps = []
    final_message = None

    payload = {"messages": [{"role": "user", "content": user_input}]}
    for step in agent.stream(payload, stream_mode="values"):
        last_msg = step["messages"][-1]
        steps.append(last_msg)
        final_message = last_msg

    final_text = getattr(final_message, "content", str(final_message))
    return final_text, steps


def describe_step(msg):
    """Formata uma mensagem intermediária do agente para exibição."""
    msg_type = getattr(msg, "type", msg.__class__.__name__)
    content = getattr(msg, "content", "")

    tool_calls = getattr(msg, "tool_calls", None)
    if tool_calls:
        lines = []
        for tc in tool_calls:
            name = tc.get("name", "ferramenta")
            args = tc.get("args", {})
            lines.append(f"🔧 **{name}**\n```\n{args}\n```")
        return "\n\n".join(lines)

    if msg_type == "tool":
        tool_name = getattr(msg, "name", "resultado")
        return f"📄 **Saída de `{tool_name}`**\n```\n{content}\n```"

    if content:
        return str(content)

    return None



with st.sidebar:
    st.markdown("### ⚙️ Conexão")

    with st.form("connection_form"):
        st.markdown("**Banco de dados PostgreSQL**")
        db_host = st.text_input("Host", value=os.getenv("DB_HOST", "localhost"))
        db_port = st.text_input("Porta", value=os.getenv("DB_PORT", "5432"))
        db_name = st.text_input(
            "Database", value=os.getenv("DB_NAME", "zepto")
        )
        db_user = st.text_input("Usuário", value=os.getenv("DB_USER", "postgres"))
        db_password = st.text_input(
            "Senha", value=os.getenv("DB_PASSWORD", ""), type="password"
        )

        st.markdown("**Modelo (OpenAI)**")
        openai_model = st.selectbox(
            "Modelo",
            options=["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini"],
            index=0,
        )
        openai_key = st.text_input(
            "OpenAI API Key",
            value=os.getenv("OPENAI_API_KEY", ""),
            type="password",
            help="Deixe em branco para usar a variável de ambiente OPENAI_API_KEY.",
        )

        submitted = st.form_submit_button("🔌 Conectar", use_container_width=True)

    if submitted:
        try:
            with st.spinner("Conectando ao banco e inicializando o agente..."):
                db, agent = build_agent(
                    db_user, db_password, db_host, db_port, db_name,
                    openai_model, openai_key,
                )
            st.session_state.db = db
            st.session_state.agent = agent
            st.session_state.connected = True
            st.session_state.messages = []
            st.success("Conectado com sucesso!")
        except Exception as e:
            st.session_state.connected = False
            st.error(f"Falha na conexão: {e}")

    st.divider()

    status_label = "🟢 Conectado" if st.session_state.connected else "🔴 Desconectado"
    status_class = "status-connected" if st.session_state.connected else "status-disconnected"
    st.markdown(
        f'<span class="status-pill {status_class}">{status_label}</span>',
        unsafe_allow_html=True,
    )

    if st.session_state.connected and st.session_state.db is not None:
        with st.expander("📋 Tabelas disponíveis"):
            try:
                st.code(st.session_state.db.get_usable_table_names())
            except Exception as e:
                st.write(f"Não foi possível listar tabelas: {e}")

    show_steps = st.toggle("Mostrar raciocínio do agente", value=False)

    st.divider()
    if st.button("🗑️ Limpar conversa", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


st.markdown(
    '<div class="app-header"><h1>🗄️ Agente SQL</h1></div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="app-subtitle">Converse em português com seu banco de dados PostgreSQL. '
    "O agente lista as tabelas, consulta o schema, escreve e executa a query por você.</div>",
    unsafe_allow_html=True,
)

if not st.session_state.connected:
    st.info("👈 Configure a conexão na barra lateral e clique em **Conectar** para começar.")


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("steps") and show_steps:
            with st.expander("🔍 Ver passos do agente"):
                for step_text in msg["steps"]:
                    st.markdown(step_text)
                    st.markdown("---")


user_input = st.chat_input(
    "Pergunte algo sobre os dados, ex: 'Quantos clientes existem na base?'",
    disabled=not st.session_state.connected,
)

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("🤔 Pensando...")
        try:
            final_text, steps = run_agent(st.session_state.agent, user_input)
            step_texts = [describe_step(s) for s in steps]
            step_texts = [t for t in step_texts if t]

            placeholder.markdown(final_text)

            if show_steps and step_texts:
                with st.expander("🔍 Ver passos do agente"):
                    for t in step_texts:
                        st.markdown(t)
                        st.markdown("---")

            st.session_state.messages.append(
                {"role": "assistant", "content": final_text, "steps": step_texts}
            )
        except Exception as e:
            error_msg = f"❌ Ocorreu um erro ao processar sua pergunta: {e}"
            placeholder.markdown(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})