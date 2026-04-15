const API = "https://ondehoje-api.onrender.com";

let listaDeRoles = [];
let imagemBase64 = ""; 
let roleAbertoId = null;

window.onload = async () => {
    iniciarGPS();
    carregarEstadosSeguro();
    carregarCategoriasSeguro();
    carregarRolesAprovados();
};

function iniciarGPS() {
    if ("geolocation" in navigator && window.location.protocol !== 'file:') {
        navigator.geolocation.getCurrentPosition(async (pos) => {
            try {
                const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${pos.coords.latitude}&lon=${pos.coords.longitude}`);
                const data = await res.json();
                document.getElementById('textoLocal').innerText = `${data.address.city || data.address.town}, ${data.address.state}`;
            } catch (e) { document.getElementById('textoLocal').innerText = "Selecionar Local"; }
        }, () => { document.getElementById('textoLocal').innerText = "Selecionar Local"; });
    } else { document.getElementById('textoLocal').innerText = "Selecionar Local"; }
}

function abrirModalLocal() { document.getElementById('modalLocal').classList.remove('hidden'); }
function fecharModalLocal() { document.getElementById('modalLocal').classList.add('hidden'); }
function salvarLocal() {
    const cid = document.getElementById('selCidade').value;
    const est = document.getElementById('selEstado').value;
    if(cid && est) { document.getElementById('textoLocal').innerText = `${cid}, ${est}`; fecharModalLocal(); } 
    else { alert("Selecione um Estado e uma Cidade!"); }
}

async function carregarCategoriasSeguro() {
    const select = document.getElementById('modCategory');
    if(!select) return;
    try {
        const res = await fetch(`${API}/categorias`);
        const categorias = await res.json();
        select.innerHTML = '<option value="">Selecione a Categoria</option>';
        categorias.forEach(c => select.innerHTML += `<option value="${c.nome}">${c.nome}</option>`);
    } catch (e) {
        select.innerHTML = '<option value="">Selecione a Categoria</option><option value="Geral">Geral</option>';
    }
}

async function carregarEstadosSeguro() {
    const selects = [document.getElementById('modEstado'), document.getElementById('selEstado')];
    try {
        const res = await fetch('https://servicodados.ibge.gov.br/api/v1/localidades/estados?orderBy=nome');
        const estados = await res.json();
        selects.forEach(select => {
            if(select) {
                select.innerHTML = '<option value="">UF</option>';
                estados.forEach(uf => select.innerHTML += `<option value="${uf.sigla}">${uf.sigla}</option>`);
            }
        });
    } catch (e) {}
}

document.addEventListener('change', async (e) => {
    if(e.target.id === 'modEstado' || e.target.id === 'selEstado'){
        const modCid = document.getElementById(e.target.id === 'modEstado' ? 'modCidade' : 'selCidade');
        modCid.innerHTML = '<option value="">Buscando...</option>';
        try {
            const res = await fetch(`https://servicodados.ibge.gov.br/api/v1/localidades/estados/${e.target.value}/municipios`);
            const cidades = await res.json();
            modCid.innerHTML = '<option value="">Selecione a Cidade</option>';
            cidades.forEach(c => modCid.innerHTML += `<option value="${c.nome}">${c.nome}</option>`);
            modCid.disabled = false;
        } catch (err) { modCid.innerHTML = '<option value="Capital">Capital</option>'; modCid.disabled = false; }
    }
});

async function curtirRole(event, btn, roleId) {
    event.stopPropagation(); 
    
    let rolesCurtidos = JSON.parse(localStorage.getItem('roles_curtidos')) || [];
    const countSpan = document.getElementById(`like-count-${roleId}`);
    let num = parseInt(countSpan.innerText);

    if (rolesCurtidos.includes(roleId)) {
        rolesCurtidos = rolesCurtidos.filter(id => id !== roleId);
        btn.classList.remove('liked');
        countSpan.innerText = num - 1;
        await fetch(`${API}/roles/like/${roleId}?acao=remove`, { method: 'POST' });
    } else {
        rolesCurtidos.push(roleId);
        btn.classList.add('liked');
        countSpan.innerText = num + 1;
        await fetch(`${API}/roles/like/${roleId}?acao=add`, { method: 'POST' });
    }
    localStorage.setItem('roles_curtidos', JSON.stringify(rolesCurtidos));
}

async function carregarRolesAprovados() {
    try {
        const res = await fetch(`${API}/roles/explorar`);
        listaDeRoles = await res.json();
        const grid = document.getElementById('eventsGrid');
        if(!grid) return;
        grid.innerHTML = '';
        
        let rolesCurtidos = JSON.parse(localStorage.getItem('roles_curtidos')) || [];

        listaDeRoles.forEach((role, i) => {
            const isLiked = rolesCurtidos.includes(role.id) ? 'liked' : '';
            grid.innerHTML += `
                <div class="card-role" onclick="abrirModalDetalhes(${i})">
                    <button class="like-btn ${isLiked}" onclick="curtirRole(event, this, ${role.id})">
                        <svg class="icon-outline" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path></svg>
                        <svg class="icon-filled" viewBox="0 0 24 24"><path d="M11.645 20.91l-.007-.003-.022-.012a15.247 15.247 0 01-.383-.218 25.18 25.18 0 01-4.244-3.17C4.688 15.36 2.25 12.174 2.25 8.25 2.25 5.322 4.714 3 7.688 3A5.5 5.5 0 0112 5.052 5.5 5.5 0 0116.313 3c2.973 0 5.437 2.322 5.437 5.25 0 3.925-2.438 7.111-4.739 9.256a25.175 25.175 0 01-4.244 3.17 15.247 15.247 0 01-.383.219l-.022.012-.007.004-.003.001a.752.752 0 01-.704 0l-.003-.001z"></path></svg>
                    </button>
                    <span id="like-count-${role.id}" class="like-count">${role.likes}</span>
                    <img src="${role.image}" class="w-full h-48 object-cover">
                    <div class="p-5">
                        <span class="text-[10px] font-black text-[#DB5227] uppercase tracking-widest">${role.category}</span>
                        <h3 class="font-black text-xl text-[#2d3748] mt-1">${role.title}</h3>
                        <p class="text-gray-500 text-xs mt-2 font-bold">📍 ${role.venue} • ${role.cidade}</p>
                    </div>
                </div>`;
        });
    } catch (e) { console.log("Erro na API."); }
}

function abrirModalDetalhes(index) {
    const r = listaDeRoles[index];
    roleAbertoId = r.id; 
    document.getElementById('detalheImagem').src = r.image;
    document.getElementById('detalheCategoria').innerText = r.category;
    document.getElementById('detalheTitulo').innerText = r.title;
    document.getElementById('detalheDesc').innerText = r.descricao || "";
    document.getElementById('detalheCidade').innerText = `${r.cidade} / ${r.estado}`;
    const btn = document.getElementById('btnComprar');
    if(r.link_ingresso) { btn.href = r.link_ingresso; btn.classList.remove('hidden'); } else { btn.classList.add('hidden'); }
    document.getElementById('modalDetalhes').classList.remove('hidden');
}

function fecharModalDetalhes() { document.getElementById('modalDetalhes').classList.add('hidden'); }
function abrirModalSugerir() { document.getElementById('modalSugerir').classList.remove('hidden'); }
function fecharModalSugerir() { document.getElementById('modalSugerir').classList.add('hidden'); document.getElementById('formSugerir').reset(); imagemBase64 = ""; }
function previewImagem(input) {
    const file = input.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            imagemBase64 = e.target.result;
            document.getElementById('previewImg').src = imagemBase64;
            document.getElementById('previewImg').classList.remove('hidden');
            document.getElementById('uploadPlaceholder').classList.add('hidden');
        }
        reader.readAsDataURL(file);
    }
}

document.addEventListener('submit', async (e) => {
    if(e.target.id === 'formSugerir') {
        e.preventDefault();
        const payload = {
            title: document.getElementById('modTitle').value, venue: document.getElementById('modVenue').value,
            estado: document.getElementById('modEstado').value, cidade: document.getElementById('modCidade').value, price: "ND",
            category: document.getElementById('modCategory').value, image: document.getElementById('modImageLink').value || "https://via.placeholder.com/400",
            descricao: document.getElementById('modDesc').value, link_ingresso: document.getElementById('modLink').value
        };
        const res = await fetch(`${API}/roles/sugerir`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
        if(res.ok) { alert("Enviado com sucesso!"); fecharModalSugerir(); }
    }
});

function share(plataforma) {
    if(!roleAbertoId) return;
    const r = listaDeRoles.find(x => x.id === roleAbertoId);
    const url = window.location.href;
    const texto = `Bora nesse rolê? ${r.title} em ${r.cidade}!`;
    fetch(`${API}/roles/share-click/${roleAbertoId}`, { method: 'POST' });
    if(plataforma === 'whatsapp') window.open(`https://api.whatsapp.com/send?text=${encodeURIComponent(texto + ' ' + url)}`);
    if(plataforma === 'facebook') window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`);
    if(plataforma === 'twitter') window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(texto)}&url=${encodeURIComponent(url)}`);
    if(plataforma === 'link') { navigator.clipboard.writeText(url); alert("Link copiado!"); }
}