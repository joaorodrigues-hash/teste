from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from pydantic import BaseModel
from typing import Optional
import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class RoleSchema(BaseModel):
    title: str
    venue: str
    estado: str
    cidade: str
    price: str
    category: str
    image: str
    descricao: Optional[str] = ""
    link_ingresso: Optional[str] = ""
    parceiro_id: Optional[int] = 0 

class ParceiroSchema(BaseModel):
    cnpj: str
    razao_social: str
    nome_fantasia: str
    email: str
    senha: str
    cidade: str
    estado: str

def iniciar_banco():
    conexao = sqlite3.connect("roles_novo.db")
    cursor = conexao.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        title TEXT, venue TEXT, estado TEXT, cidade TEXT,
        price TEXT, category TEXT, image TEXT, descricao TEXT, link_ingresso TEXT, 
        likes INTEGER DEFAULT 0, clicks_share INTEGER DEFAULT 0, 
        status TEXT DEFAULT 'pendente', data_criacao TEXT, parceiro_id INTEGER DEFAULT 0)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS parceiros (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        cnpj TEXT UNIQUE, razao_social TEXT, nome_fantasia TEXT,
        email TEXT UNIQUE, senha TEXT, cidade TEXT, estado TEXT, 
        nome TEXT DEFAULT '', sobrenome TEXT DEFAULT '', foto TEXT DEFAULT '')''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, senha TEXT, nome TEXT, sobrenome TEXT)''')
    
    cursor.execute("SELECT COUNT(*) FROM admin")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO admin (email, senha, nome, sobrenome) VALUES ('admin@admin.com', 'mestre123', 'Admin', 'Master')")

    cursor.execute('''CREATE TABLE IF NOT EXISTS categorias (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)''')
    cursor.execute("SELECT COUNT(*) FROM categorias")
    if cursor.fetchone()[0] == 0:
        for cat in ["Festas", "Sertanejo", "Música ao Vivo", "Eletrônica", "Rock", "Samba"]:
            cursor.execute("INSERT INTO categorias (nome) VALUES (?)", (cat,))
            
    conexao.commit()
    conexao.close()

iniciar_banco()

# --- ADMIN ROTAS ---
@app.post("/admin/login")
def admin_login(dados: dict):
    conexao = sqlite3.connect("roles_novo.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT id, nome, sobrenome, email FROM admin WHERE senha=?", (dados["senha"],))
    admin = cursor.fetchone()
    conexao.close()
    if admin: return {"id": admin[0], "nome": admin[1], "sobrenome": admin[2], "email": admin[3]}
    raise HTTPException(status_code=401, detail="Senha incorreta")

@app.post("/admin/perfil")
def admin_perfil(dados: dict):
    conexao = sqlite3.connect("roles_novo.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT senha FROM admin WHERE id=1")
    senha_atual = cursor.fetchone()[0]
    if dados["senha_antiga"] and dados["senha_antiga"] != senha_atual:
        raise HTTPException(status_code=400, detail="Senha antiga incorreta")
    nova_senha = dados["senha_nova"] if dados["senha_nova"] else senha_atual
    cursor.execute("UPDATE admin SET nome=?, sobrenome=?, email=?, senha=? WHERE id=1", 
                  (dados["nome"], dados["sobrenome"], dados["email"], nova_senha))
    conexao.commit()
    conexao.close()
    return {"status": "ok"}

@app.get("/admin/stats")
def stats_admin():
    try:
        conexao = sqlite3.connect("roles_novo.db")
        cursor = conexao.cursor()
        cursor.execute("SELECT COUNT(*) FROM roles WHERE status='aprovado'")
        ativos = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM roles WHERE status='pendente'")
        pendentes = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(likes) FROM roles")
        total_likes = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(clicks_share) FROM roles")
        total_shares = cursor.fetchone()[0] or 0
        conexao.close()
        return {"aprovados": ativos, "pendentes": pendentes, "total_likes": total_likes, "total_shares": total_shares}
    except Exception as e:
        return {"aprovados": 0, "pendentes": 0, "total_likes": 0, "total_shares": 0}

# --- PARCEIROS ROTAS ---
@app.post("/parceiros/registrar")
def registrar_parceiro(p: ParceiroSchema):
    try:
        conexao = sqlite3.connect("roles_novo.db")
        cursor = conexao.cursor()
        cursor.execute("INSERT INTO parceiros (cnpj, razao_social, nome_fantasia, email, senha, cidade, estado) VALUES (?, ?, ?, ?, ?, ?, ?)", 
            (p.cnpj, p.razao_social, p.nome_fantasia, p.email, p.senha, p.cidade, p.estado))
        conexao.commit()
        conexao.close()
        return {"mensagem": "Sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="E-mail ou CNPJ já cadastrados.")

@app.post("/parceiros/login")
def login_parceiro(dados: dict):
    conexao = sqlite3.connect("roles_novo.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT id, nome_fantasia, nome, sobrenome, email FROM parceiros WHERE email=? AND senha=?", (dados["email"], dados["senha"]))
    user = cursor.fetchone()
    conexao.close()
    if user: return {"id": user[0], "empresa": user[1], "nome": user[2], "sobrenome": user[3], "email": user[4]}
    raise HTTPException(status_code=401, detail="Email ou senha incorretos")

@app.get("/parceiros/stats/{id}")
def stats_parceiro(id: int):
    conexao = sqlite3.connect("roles_novo.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT COUNT(*) FROM roles WHERE parceiro_id=?", (id,))
    sugeridos = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(likes), SUM(clicks_share) FROM roles WHERE parceiro_id=?", (id,))
    soma = cursor.fetchone()
    conexao.close()
    return {"sugeridos": sugeridos, "likes": soma[0] or 0, "shares": soma[1] or 0}

@app.post("/parceiros/perfil/{id}")
def perfil_parceiro(id: int, dados: dict):
    conexao = sqlite3.connect("roles_novo.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT senha FROM parceiros WHERE id=?", (id,))
    senha_atual = cursor.fetchone()[0]
    if dados["senha_antiga"] and dados["senha_antiga"] != senha_atual:
        raise HTTPException(status_code=400, detail="Senha antiga incorreta")
    nova_senha = dados["senha_nova"] if dados["senha_nova"] else senha_atual
    cursor.execute("UPDATE parceiros SET nome=?, sobrenome=?, email=?, senha=? WHERE id=?", 
                  (dados["nome"], dados["sobrenome"], dados["email"], nova_senha, id))
    conexao.commit()
    conexao.close()
    return {"status": "ok"}

@app.get("/parceiros/lista")
def listar_parceiros():
    conexao = sqlite3.connect("roles_novo.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT cnpj, nome_fantasia, email, senha, cidade, estado FROM parceiros")
    p = cursor.fetchall()
    conexao.close()
    return [{"cnpj": r[0], "nome": r[1], "email": r[2], "senha": r[3], "cidade": r[4], "estado": r[5]} for r in p]

# --- CATEGORIAS ---
@app.get("/categorias")
def listar_categorias():
    conexao = sqlite3.connect("roles_novo.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT id, nome FROM categorias ORDER BY nome")
    cats = [{"id": r[0], "nome": r[1]} for r in cursor.fetchall()]
    conexao.close()
    return cats

@app.post("/categorias/add")
def adicionar_categoria(data: dict):
    try:
        conexao = sqlite3.connect("roles_novo.db")
        cursor = conexao.cursor()
        cursor.execute("INSERT INTO categorias (nome) VALUES (?)", (data["nome"],))
        conexao.commit()
        conexao.close()
        return {"status": "ok"}
    except:
        raise HTTPException(status_code=400, detail="Categoria já existe.")

@app.post("/categorias/delete/{id}")
def deletar_categoria(id: int):
    conexao = sqlite3.connect("roles_novo.db")
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM categorias WHERE id = ?", (id,))
    conexao.commit()
    conexao.close()
    return {"status": "ok"}

# --- ROLÊS (EVENTOS) ---
@app.post("/roles/sugerir")
def sugerir_role(data: RoleSchema):
    hoje = datetime.date.today().strftime("%Y-%m-%d")
    conexao = sqlite3.connect("roles_novo.db")
    cursor = conexao.cursor()
    cursor.execute('''INSERT INTO roles (title, venue, estado, cidade, price, category, image, descricao, link_ingresso, status, data_criacao, parceiro_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pendente', ?, ?)''', 
        (data.title, data.venue, data.estado, data.cidade, data.price, data.category, data.image, data.descricao, data.link_ingresso, hoje, data.parceiro_id))
    conexao.commit()
    conexao.close()
    return {"mensagem": "Sugerido"}

@app.get("/roles/explorar")
def explorar_roles():
    conexao = sqlite3.connect("roles_novo.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT id, title, venue, estado, cidade, price, category, image, descricao, link_ingresso, likes FROM roles WHERE status='aprovado'")
    r = cursor.fetchall()
    conexao.close()
    return [{"id": x[0], "title": x[1], "venue": x[2], "estado": x[3], "cidade": x[4], "price": x[5], "category": x[6], "image": x[7], "descricao": x[8], "link_ingresso": x[9], "likes": x[10]} for x in r]

@app.post("/roles/like/{role_id}")
def curtir_role(role_id: int, acao: str):
    conexao = sqlite3.connect("roles_novo.db")
    cursor = conexao.cursor()
    if acao == "add": cursor.execute("UPDATE roles SET likes = likes + 1 WHERE id=?", (role_id,))
    else: cursor.execute("UPDATE roles SET likes = MAX(0, likes - 1) WHERE id=?", (role_id,))
    conexao.commit()
    conexao.close()
    return {"status": "ok"}

@app.post("/roles/share-click/{role_id}")
def contar_share(role_id: int):
    conexao = sqlite3.connect("roles_novo.db")
    cursor = conexao.cursor()
    cursor.execute("UPDATE roles SET clicks_share = clicks_share + 1 WHERE id=?", (role_id,))
    conexao.commit()
    conexao.close()
    return {"status": "ok"}

@app.get("/roles/pendentes")
def listar_pendentes():
    conexao = sqlite3.connect("roles_novo.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT id, title, venue, estado, cidade, image, category FROM roles WHERE status='pendente'")
    p = cursor.fetchall()
    conexao.close()
    return [{"id": r[0], "title": r[1], "venue": r[2], "estado": r[3], "cidade": r[4], "image": r[5], "category": r[6]} for r in p]

@app.post("/roles/aprovar/{id}")
def aprovar(id: int):
    conexao = sqlite3.connect("roles_novo.db")
    cursor = conexao.cursor()
    cursor.execute("UPDATE roles SET status='aprovado' WHERE id=?", (id,))
    conexao.commit()
    conexao.close()
    return {"status": "ok"}

@app.post("/roles/rejeitar/{id}")
def rejeitar(id: int):
    conexao = sqlite3.connect("roles_novo.db")
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM roles WHERE id=?", (id,))
    conexao.commit()
    conexao.close()
    return {"status": "ok"}

# NOVA ROTA: GERENCIAR EVENTOS APROVADOS OU OCULTOS
@app.get("/roles/gerenciar")
def gerenciar_roles():
    conexao = sqlite3.connect("roles_novo.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT id, title, venue, cidade, estado, image, status FROM roles WHERE status IN ('aprovado', 'oculto')")
    p = cursor.fetchall()
    conexao.close()
    return [{"id": r[0], "title": r[1], "venue": r[2], "cidade": r[3], "estado": r[4], "image": r[5], "status": r[6]} for r in p]

# NOVA ROTA: MUDAR STATUS (OCULTAR / EXIBIR / EXCLUIR)
@app.post("/roles/status/{id}")
def mudar_status(id: int, dados: dict):
    conexao = sqlite3.connect("roles_novo.db")
    cursor = conexao.cursor()
    if dados["status"] == "excluir":
        cursor.execute("DELETE FROM roles WHERE id=?", (id,))
    else:
        cursor.execute("UPDATE roles SET status=? WHERE id=?", (dados["status"], id))
    conexao.commit()
    conexao.close()
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)