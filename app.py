import io
import re
import unicodedata
from pathlib import Path
from xml.sax.saxutils import escape

import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable

st.set_page_config(page_title="Criador de Currículo", page_icon="📄", layout="centered")
st.title("📄 Meu Currículo Profissional")
st.caption("Responda às perguntas e baixe seu currículo em PDF, sem precisar criar uma conta.")

ETAPAS = ["Informações", "Sobre mim", "Ensino Fundamental", "Ensino Médio", "Formação Técnica e Cursos", "Formação Superior", "Pós-graduação", "Experiência Profissional", "Trabalho Voluntário", "Minhas Habilidades", "Conclusão", "Seu currículo"]
HABILIDADES = [
    "Pensamento analítico", "Resolução de problemas complexos", "Criatividade", "Resiliência",
    "Flexibilidade em aprender", "Agilidade", "Motivação", "Autoconsciência", "Comunicação",
    "Fluência tecnológica e digital", "Confiabilidade e atenção aos detalhes", "Empatia e escuta ativa",
    "Liderança e influência social", "Controle de qualidade", "Pensamento organizado",
    "Gestão de tempo e organização", "Atendimento ao cliente", "IA e big data",
    "Habilidade socioemocional", "Comprometimento", "Proatividade e autonomia",
    "Trabalho em equipe e colaboração",
]


def inicializar():
    if "curriculo" not in st.session_state:
        st.session_state.curriculo = {
            "nome": "", "email": "", "whatsapp": "", "sobre": "", "fundamental": None,
            "medio": None, "tecnicos": [], "superiores": [], "pos": [],
            "experiencias": [], "voluntarios": [], "habilidades": [], "conclusao": ""
        }
        st.session_state.etapa_cv = 0
        st.session_state.pendente_cv = None


def avancar():
    st.session_state.etapa_cv += 1
    st.session_state.pendente_cv = None
    st.rerun()


def anterior():
    st.session_state.etapa_cv = max(0, st.session_state.etapa_cv - 1)
    st.session_state.pendente_cv = None
    st.rerun()


def ano_valido(valor):
    return bool(re.fullmatch(r"\d{4}", valor.strip())) and 1950 <= int(valor.strip()) <= 2150


def campo_ano(rotulo, chave, obrigatorio=True, valor=""):
    return st.text_input(rotulo, value=valor, placeholder="Ex.: 2026", key=chave).strip()


def validar_ano(ano, obrigatorio=True):
    if (not ano and not obrigatorio) or ano_valido(ano):
        return True
    st.warning("Informe o ano com quatro números, por exemplo: 2026.")
    return False


def texto_obrigatorio(*valores):
    if any(not v.strip() for v in valores):
        st.warning("Preencha todos os campos obrigatórios desta etapa.")
        return False
    return True


def mostrar_resumo(itens, titulo):
    if itens:
        st.markdown(f"**{titulo} já adicionados:** {len(itens)}")
        for i, item in enumerate(itens, 1):
            st.caption(f"{i}. {item.get('curso') or item.get('empresa') or item.get('descricao')}")


def formulario_curso(chave, titulo, pergunta):
    lista = st.session_state.curriculo[chave]
    st.subheader(titulo)
    mostrar_resumo(lista, "Registros")
    if not lista:
        escolha = st.radio(pergunta, ["Sim", "Não"], index=None, key=f"pergunta_{chave}")
        if escolha == "Não":
            if st.button("Continuar sem adicionar", key=f"pular_{chave}"):
                avancar()
            return
        if escolha is None:
            return
    with st.form(f"curso_{chave}", clear_on_submit=True):
        curso = st.text_input("Qual o nome ou área do curso?")
        instituicao = st.text_input("Por qual instituição?")
        situacao = st.radio("Qual a situação do curso?", ["Em andamento", "Concluído"], horizontal=True)
        ano = st.text_input("Qual o ano de conclusão (ou previsão)?", placeholder="Ex.: 2027")
        c1, c2 = st.columns(2)
        adicionar = c1.form_submit_button("Salvar e adicionar outro")
        concluir = c2.form_submit_button("Salvar e continuar")
    if adicionar or concluir:
        if texto_obrigatorio(curso, instituicao) and validar_ano(ano):
            lista.append({"curso": curso.strip(), "instituicao": instituicao.strip(), "situacao": situacao, "ano": ano})
            if concluir:
                avancar()
            else:
                st.rerun()
    if lista and st.button("Continuar sem adicionar outro", key=f"seguir_{chave}"):
        avancar()


def formulario_experiencia():
    lista = st.session_state.curriculo["experiencias"]
    st.subheader("Etapa 8 — Experiência Profissional")
    mostrar_resumo(lista, "Experiências")
    if not lista:
        resposta = st.radio("Você possui experiência profissional?", ["Sim", "Não"], index=None, key="tem_exp")
        if resposta == "Não":
            if st.button("Ir para trabalho voluntário"):
                avancar()
            return
        if resposta is None:
            return
    # O radio fica fora do formulário para mostrar imediatamente os campos condicionais.
    atual = st.radio("É o seu trabalho atual?", ["Sim", "Não"], index=None, horizontal=True, key="exp_atual")
    with st.form("form_experiencia", clear_on_submit=True):
        empresa = st.text_input("Em qual empresa?")
        inicio = st.text_input("Em que ano começou a trabalhar nesta empresa?", placeholder="Ex.: 2022")
        fim_mes, fim_ano = "", ""
        if atual == "Não":
            fim_mes = st.selectbox("Até que mês você trabalhou lá?", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"])
            fim_ano = st.text_input("Até que ano?", placeholder="Ex.: 2024")
        carteira = st.radio("Com registro em carteira?", ["Sim", "Não"], horizontal=True)
        vinculo = st.radio("Como profissional ou aprendiz?", ["Profissional", "Aprendiz"], horizontal=True)
        area = st.text_input("Em que área você atuava?")
        funcao = st.text_input("Qual era sua função nesta empresa?")
        c1, c2 = st.columns(2)
        adicionar = c1.form_submit_button("Salvar e adicionar outra")
        concluir = c2.form_submit_button("Salvar e continuar")
    if adicionar or concluir:
        if atual is None:
            st.warning("Informe se este é seu trabalho atual.")
        elif texto_obrigatorio(empresa, area, funcao) and validar_ano(inicio) and (atual == "Sim" or validar_ano(fim_ano)):
            if atual == "Não" and int(fim_ano) < int(inicio):
                st.warning("O ano de término não pode ser anterior ao início.")
            else:
                lista.append({"empresa": empresa.strip(), "inicio": inicio, "atual": atual == "Sim",
                              "fim_mes": fim_mes, "fim_ano": fim_ano, "carteira": carteira,
                              "vinculo": vinculo, "area": area.strip(), "funcao": funcao.strip()})
                if concluir:
                    avancar()
                else:
                    st.session_state.pop("exp_atual", None)
                    st.rerun()
    if lista and st.button("Continuar sem adicionar outra experiência"):
        avancar()


def formulario_voluntariado():
    lista = st.session_state.curriculo["voluntarios"]
    st.subheader("Etapa 9 — Trabalho Voluntário")
    mostrar_resumo(lista, "Trabalhos voluntários")
    if not lista:
        resposta = st.radio("Já fez algum trabalho voluntário?", ["Sim", "Não"], index=None, key="tem_vol")
        if resposta == "Não":
            if st.button("Ir para habilidades"):
                avancar()
            return
        if resposta is None:
            return
    atual = st.radio("Você ainda faz este trabalho?", ["Sim", "Não"], index=None, horizontal=True, key="vol_atual")
    with st.form("form_voluntariado", clear_on_submit=True):
        descricao = st.text_area("Conte em poucas palavras qual o tipo de trabalho.")
        fim_mes, fim_ano = "", ""
        if atual == "Não":
            fim_mes = st.selectbox("Até que mês você atuou?", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"])
            fim_ano = st.text_input("Até que ano?", placeholder="Ex.: 2025")
        c1, c2 = st.columns(2)
        adicionar = c1.form_submit_button("Salvar e adicionar outro")
        concluir = c2.form_submit_button("Salvar e continuar")
    if adicionar or concluir:
        if atual is None:
            st.warning("Informe se ainda realiza este trabalho voluntário.")
        elif texto_obrigatorio(descricao) and (atual == "Sim" or validar_ano(fim_ano)):
            lista.append({"descricao": descricao.strip(), "atual": atual == "Sim", "fim_mes": fim_mes, "fim_ano": fim_ano})
            if concluir:
                avancar()
            else:
                st.rerun()
    if lista and st.button("Continuar sem adicionar outro voluntariado"):
        avancar()


def fonte_pdf():
    caminhos = [
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf", "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf")
    ]
    for normal, negrito in caminhos:
        if Path(normal).exists() and Path(negrito).exists():
            if "CVNormal" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("CVNormal", normal))
                pdfmetrics.registerFont(TTFont("CVBold", negrito))
            return "CVNormal", "CVBold"
    return "Helvetica", "Helvetica-Bold"


def gerar_pdf(dados):
    buffer = io.BytesIO()
    normal, bold = fonte_pdf()
    estilo_nome = ParagraphStyle("NomeCV", fontName=bold, fontSize=19, leading=23, textColor=colors.HexColor("#153751"), spaceAfter=7)
    estilo_corpo = ParagraphStyle("CorpoCV", fontName=normal, fontSize=9.2, leading=14, spaceAfter=5)
    estilo_secao = ParagraphStyle("SecaoCV", fontName=bold, fontSize=10, leading=15, textColor=colors.HexColor("#153751"), spaceBefore=15, spaceAfter=6, keepWithNext=True)
    estilo_item = ParagraphStyle("ItemCV", fontName=bold, fontSize=9.5, leading=14, spaceBefore=6, spaceAfter=3)
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=48, leftMargin=48, topMargin=44, bottomMargin=48, title="CURRÍCULO")
    historia = [Paragraph("CURRÍCULO", ParagraphStyle("CapCV", fontName=bold, fontSize=10, leading=14, textColor=colors.grey, spaceAfter=7)),
                Paragraph(escape(dados["nome"]), estilo_nome),
                Paragraph(f"{escape(dados['email'])}  |  WhatsApp: {escape(dados['whatsapp'])}", estilo_corpo),
                Spacer(1, 9), HRFlowable(width="100%", thickness=1, color=colors.HexColor("#D7E2EB"))]

    def secao(titulo):
        historia.append(Paragraph(escape(titulo.upper()), estilo_secao))

    def linha(texto):
        historia.append(Paragraph(escape(str(texto)).replace("\n", "<br/>"), estilo_corpo))

    if dados["sobre"]:
        secao("Sobre mim")
        linha(dados["sobre"])

    if dados["fundamental"]:
        secao("Ensino Fundamental")
        f = dados["fundamental"]
        linha(f"Concluído — {f['escola']} | {f['ano']}")

    if dados["medio"]:
        secao("Ensino Médio")
        m = dados["medio"]
        if m["concluido"]:
            linha(f"Concluído — {m['escola']} | {m['ano']}")
        else:
            linha(f"Em andamento — {m['serie']} | Conclusão prevista: {m['ano']}")

    for chave, titulo in [("tecnicos", "Cursos e Formação Técnica"), ("superiores", "Formação Superior"), ("pos", "Pós-graduação")]:
        if dados[chave]:
            secao(titulo)
            for item in dados[chave]:
                historia.append(Paragraph(escape(item["curso"]), estilo_item))
                linha(f"{item['instituicao']} — {item['situacao']} | Ano: {item['ano']}")

    if dados["experiencias"]:
        secao("Experiência Profissional")
        for exp in dados["experiencias"]:
            historia.append(Paragraph(escape(exp["empresa"]), estilo_item))
            periodo = f"{exp['inicio']} — " + ("Atual" if exp["atual"] else f"{exp['fim_mes']}/{exp['fim_ano']}")
            linha(f"{exp['funcao']} | {exp['area']} | {periodo}")
            linha(f"Vínculo: {exp['vinculo']} | Registro em carteira: {exp['carteira']}")

    if dados["voluntarios"]:
        secao("Trabalho Voluntário")
        for item in dados["voluntarios"]:
            linha(item["descricao"] + " — " + ("Atualmente" if item["atual"] else f"Até {item['fim_mes']}/{item['fim_ano']}"))

    if dados["habilidades"]:
        secao("Minhas Habilidades")
        linha(" • ".join(dados["habilidades"]))

    if dados["conclusao"]:
        secao("Compromisso Profissional")
        linha(dados["conclusao"])

    doc.build(historia)
    return buffer.getvalue()


inicializar()
dados = st.session_state.curriculo
etapa = st.session_state.etapa_cv
st.progress(etapa / (len(ETAPAS) - 1), text=f"Etapa {min(etapa + 1, 11)} de 11 — {ETAPAS[etapa]}")
if etapa > 0 and etapa < 11:
    if st.button("← Voltar à etapa anterior"):
        anterior()

if etapa == 0:
    st.info("Olá, estou aqui para te ajudar a criar seu currículo e permitir que você baixe em PDF. As perguntas vão gerar informações que vão te ajudar.")
    st.subheader("Etapa 1 — Informações")
    with st.form("informacoes"):
        nome = st.text_input("Qual é o seu nome completo?", value=dados["nome"])
        email = st.text_input("Perfeito! Agora escreva o seu e-mail.", value=dados["email"])
        whats = st.text_input("Digite seu contato do WhatsApp (com DDD).", value=dados["whatsapp"])
        ok = st.form_submit_button("Continuar")
    if ok:
        if not texto_obrigatorio(nome, email, whats):
            pass
        elif not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email.strip()):
            st.warning("Confira o formato do e-mail.")
        else:
            dados.update(nome=nome.strip(), email=email.strip(), whatsapp=whats.strip())
            avancar()

elif etapa == 1:
    st.subheader("Etapa 2 — Sobre mim")
    with st.form("sobre"):
        sobre = st.text_area(f"Perfeito, {dados['nome']}! Conte algo interessante sobre você: uma habilidade, um objetivo ou aquilo que pretende se tornar.", value=dados["sobre"], height=150)
        ok = st.form_submit_button("OK — Continuar")
    if ok:
        dados["sobre"] = sobre.strip()
        avancar()

elif etapa == 2:
    st.subheader("Etapa 3 — Ensino Fundamental")
    concluiu = st.radio("Você já concluiu o Ensino Fundamental?", ["Sim", "Não"],
                        index=None, key="fund_concluiu")
    with st.form("fundamental"):
        escola = st.text_input("Em qual escola?", value=(dados["fundamental"] or {}).get("escola", "")) if concluiu == "Sim" else ""
        ano = st.text_input("Em que ano terminou?", placeholder="Ex.: 2020", value=(dados["fundamental"] or {}).get("ano", "")) if concluiu == "Sim" else ""
        ok = st.form_submit_button("Continuar")
    if ok:
        if concluiu is None:
            st.warning("Escolha Sim ou Não.")
        elif concluiu == "Não":
            dados["fundamental"] = None
            avancar()
        elif texto_obrigatorio(escola) and validar_ano(ano):
            dados["fundamental"] = {"escola": escola.strip(), "ano": ano}
            avancar()

elif etapa == 3:
    st.subheader("Etapa 4 — Ensino Médio")
    anterior_m = dados["medio"] or {}
    concluiu = st.radio("Você já concluiu o Ensino Médio?", ["Sim", "Não"], index=None, key="medio_concluiu")
    with st.form("medio"):
        escola, serie, ano = "", "", ""
        if concluiu == "Sim":
            escola = st.text_input("Em qual escola?", value=anterior_m.get("escola", ""))
            ano = st.text_input("Em que ano terminou?", placeholder="Ex.: 2024", value=anterior_m.get("ano", ""))
        elif concluiu == "Não":
            serie = st.selectbox("Em que ano você está?", ["1º ano", "2º ano", "3º ano"])
            ano = st.text_input("Em que ano você concluirá o Ensino Médio?", placeholder="Ex.: 2027", value=anterior_m.get("ano", ""))
        ok = st.form_submit_button("Continuar")
    if ok:
        if concluiu is None:
            st.warning("Escolha Sim ou Não.")
        elif validar_ano(ano) and (concluiu == "Não" or texto_obrigatorio(escola)):
            dados["medio"] = {"concluido": concluiu == "Sim", "escola": escola.strip(), "serie": serie, "ano": ano}
            avancar()

elif etapa == 4:
    formulario_curso("tecnicos", "Etapa 5 — Formação Técnica e Cursos", "Você já fez algum curso técnico, online ou presencial?")

elif etapa == 5:
    formulario_curso("superiores", "Etapa 6 — Formação Superior", "Você cursa ou já concluiu Ensino Superior?")

elif etapa == 6:
    formulario_curso("pos", "Etapa 7 — Pós-graduação", "Você cursa ou já concluiu alguma pós-graduação?")

elif etapa == 7:
    formulario_experiencia()

elif etapa == 8:
    formulario_voluntariado()

elif etapa == 9:
    st.subheader("Etapa 10 — Minhas Habilidades")
    st.write("Assinale as habilidades que mais têm a ver com você:")
    with st.form("habilidades"):
        habilidades = st.multiselect("Selecione suas habilidades", HABILIDADES, default=dados["habilidades"])
        ok = st.form_submit_button("Continuar")
    if ok:
        dados["habilidades"] = habilidades
        avancar()

elif etapa == 10:
    st.subheader("Etapa 11 — Conclusão")
    with st.form("conclusao"):
        conclusao = st.text_area("Escreva em poucas palavras como pretende se comprometer caso seja contratado.", value=dados["conclusao"], height=145)
        ok = st.form_submit_button("Gerar meu currículo")
    if ok:
        dados["conclusao"] = conclusao.strip()
        avancar()

elif etapa == 11:
    st.success(f"Parabéns, {dados['nome']}! Seu currículo está pronto.")
    st.subheader("Prévia dos dados do currículo")
    st.markdown(f"**Nome:** {dados['nome']}")
    st.write(f"**E-mail:** {dados['email']} | **WhatsApp:** {dados['whatsapp']}")
    if dados["sobre"]:
        st.markdown("**Sobre mim**")
        st.write(dados["sobre"])
    if dados["fundamental"]:
        st.write("**Ensino Fundamental:**", dados["fundamental"]["escola"], dados["fundamental"]["ano"])
    if dados["medio"]:
        st.write("**Ensino Médio:**", dados["medio"])
    for chave, rotulo in [("tecnicos", "Cursos"), ("superiores", "Superior"), ("pos", "Pós-graduação"), ("experiencias", "Experiências"), ("voluntarios", "Voluntariado")]:
        if dados[chave]:
            st.write(f"**{rotulo}:** {len(dados[chave])} registro(s)")
    if dados["habilidades"]:
        st.write("**Habilidades:**", ", ".join(dados["habilidades"]))
    if dados["conclusao"]:
        st.markdown("**Compromisso profissional**")
        st.write(dados["conclusao"])
    try:
        pdf = gerar_pdf(dados)
        nome_arquivo = re.sub(r"[^a-z0-9]+", "_", unicodedata.normalize("NFKD", dados["nome"]).encode("ascii", "ignore").decode().lower()).strip("_") or "participante"
        st.download_button("⬇️ BAIXAR MEU CURRÍCULO EM PDF", data=pdf, file_name=f"curriculo_{nome_arquivo}.pdf", mime="application/pdf", type="primary", use_container_width=True)
    except Exception:
        st.error("Não foi possível gerar o PDF. Confira as dependências e tente novamente.")
    if st.button("🔄 Criar outro currículo"):
        for chave in ["curriculo", "etapa_cv", "pendente_cv"]:
            st.session_state.pop(chave, None)
        st.rerun()

st.caption("Os dados são usados para gerar o currículo durante a sessão. Este aplicativo não envia e-mails nem possui banco de dados. Compartilhe apenas informações que deseja incluir no currículo.")
