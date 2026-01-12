from flask import Flask, request, redirect, url_for, render_template_string, send_file, jsonify
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import os
import json
import threading
import time
import requests
import socket
from datetime import datetime
import logging 
import qrcode # Garante que está importado

# ============================================================================
# CONFIGURAÇÃO DE HARDWARE
# ============================================================================
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

USAR_VERSAO_V2 = True 
try:
    if USAR_VERSAO_V2: from waveshare_epd import epd7in5_V2 as epd_driver
    else: from waveshare_epd import epd7in5 as epd_driver
    HAS_SCREEN = True
    print("[BOOT] E-Ink Detetado.")
except:
    print("[BOOT] Modo Simulação.")
    HAS_SCREEN = False

app = Flask(__name__)
screen_lock = threading.Lock()

# ============================================================================
# CONFIGURAÇÕES
# ============================================================================
ARQUIVO_CONFIG = 'config_cripto.json'
WIDTH, HEIGHT = 800, 480

CRYPTOS = {
    "BTC": {"nome": "Bitcoin", "icone": "https://cryptologos.cc/logos/bitcoin-btc-logo.png"},
    "ETH": {"nome": "Ethereum", "icone": "https://cryptologos.cc/logos/ethereum-eth-logo.png"},
    "SOL": {"nome": "Solana", "icone": "https://cryptologos.cc/logos/solana-sol-logo.png"},
    "XRP": {"nome": "XRP", "icone": "https://cryptologos.cc/logos/xrp-xrp-logo.png"},
    "ADA": {"nome": "Cardano", "icone": "https://cryptologos.cc/logos/cardano-ada-logo.png"},
    "DOGE": {"nome": "Dogecoin", "icone": "https://cryptologos.cc/logos/dogecoin-doge-logo.png"},
    "DOT": {"nome": "Polkadot", "icone": "https://cryptologos.cc/logos/polkadot-new-dot-logo.png"},
    "MATIC": {"nome": "Polygon", "icone": "https://cryptologos.cc/logos/polygon-matic-logo.png"},
    "PEPE": {"nome": "Pepe", "icone": "https://cryptologos.cc/logos/pepe-pepe-logo.png"},
    "SHIB": {"nome": "Shiba Inu", "icone": "https://cryptologos.cc/logos/shiba-inu-shib-logo.png"}
}

DEFAULT_CONFIG = { "coin": "BTC", "fiat": "BRL", "intervalo": 60, "dark_mode": True }

CACHE_DADOS = {
    "preco": 0.0, "high": 0.0, "low": 0.0, "change": 0.0,
    "historico": [], "last_update": 0, "usd_brl": 0.0,
    "nome_display": "Bitcoin", "simbolo_display": "BTC/BRL"
}

STATUS = { "ocupado": False, "msg": "Iniciando...", "last_update_str": "--:--" }

# ============================================================================
# API BINANCE
# ============================================================================
def obter_cotacao_dolar():
    try:
        r = requests.get("https://economia.awesomeapi.com.br/last/USD-BRL", timeout=2)
        return float(r.json()['USDBRL']['bid'])
    except: return 0.0

def obter_dados_binance(coin, fiat):
    symbol = f"{coin}{fiat}".upper()
    if fiat == "USD": symbol = f"{coin}USDT" 
    
    print(f"[API] Consultando Binance: {symbol}...")
    try:
        r = requests.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}", timeout=5)
        if r.status_code != 200: return None
        data = r.json()
        
        r_kline = requests.get(f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=24", timeout=5)
        candles = r_kline.json()
        historico_res = [float(c[4]) for c in candles]

        return {
            "preco": float(data['lastPrice']),
            "change": float(data['priceChangePercent']),
            "high": float(data['highPrice']),
            "low": float(data['lowPrice']),
            "historico": historico_res
        }
    except Exception as e:
        print(f"[ERRO API] {e}")
        return None

def carregar_config():
    if not os.path.exists(ARQUIVO_CONFIG): return DEFAULT_CONFIG.copy()
    try:
        with open(ARQUIVO_CONFIG, 'r') as f:
            c = json.load(f)
            if 'coin' not in c: return DEFAULT_CONFIG.copy()
            return c
    except: return DEFAULT_CONFIG.copy()

def salvar_config(conf):
    with open(ARQUIVO_CONFIG, 'w') as f: json.dump(conf, f, indent=4)

def atualizar_dados(force=False):
    global CACHE_DADOS, STATUS
    conf = carregar_config()
    
    intervalo = conf.get('intervalo', 60)
    if intervalo < 10: intervalo = 10
    
    if not force and (time.time() - CACHE_DADOS['last_update'] < intervalo): return True

    STATUS["msg"] = "Conectando Binance..."
    dados = obter_dados_binance(conf['coin'], conf['fiat'])
    
    if dados:
        CACHE_DADOS.update(dados)
        CACHE_DADOS['nome_display'] = CRYPTOS[conf['coin']]['nome']
        CACHE_DADOS['simbolo_display'] = f"{conf['coin']}/{conf['fiat']}".upper()
        CACHE_DADOS['usd_brl'] = obter_cotacao_dolar()
        CACHE_DADOS['last_update'] = time.time()
        STATUS['last_update_str'] = datetime.now().strftime("%H:%M:%S")
        STATUS["msg"] = "Dados Recebidos."
        print(f"[SUCESSO] Preço Atual: {dados['preco']}")
        return True
    else:
        STATUS["msg"] = "Erro Binance"
        return False

# ============================================================================
# MOTOR GRÁFICO
# ============================================================================
def carregar_fontes():
    base = '/usr/share/fonts/truetype/dejavu/DejaVuSans'
    try:
        ImageFont.truetype(f'{base}-Bold.ttf', 10)
        return {
            'huge': ImageFont.truetype(f'{base}-Bold.ttf', 70),
            'large': ImageFont.truetype(f'{base}-Bold.ttf', 55),
            'big': ImageFont.truetype(f'{base}-Bold.ttf', 35),
            'med': ImageFont.truetype(f'{base}.ttf', 24),
            'small': ImageFont.truetype(f'{base}.ttf', 18)
        }
    except:
        d = ImageFont.load_default()
        return {'huge':d, 'large':d, 'big':d, 'med':d, 'small':d}

def baixar_icone(coin_code, inverted=False):
    try:
        url = CRYPTOS[coin_code]['icone']
        cache_file = f"icon_{coin_code}.png"
        
        if not os.path.exists(cache_file):
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            with open(cache_file, 'wb') as f: f.write(r.content)
            
        img = Image.open(cache_file).convert("RGBA")
        bg_col = (0,0,0) if inverted else (255,255,255)
        bg = Image.new("RGBA", img.size, bg_col)
        img = Image.alpha_composite(bg, img).convert("RGB")
        
        return img.resize((70, 70))
    except: return None

def desenhar_grafico_manual(draw, dados, area, cor_linha):
    x_start, y_start, w, h = area
    if not dados or len(dados) < 2: return
    min_val, max_val = min(dados), max(dados)
    diff = max_val - min_val
    if diff == 0: diff = 1
    step_x = w / (len(dados) - 1)
    coords = []
    for i, val in enumerate(dados):
        x = x_start + (i * step_x)
        y = y_start + h - ((val - min_val) / diff * h)
        coords.append((x, y))
    draw.line(coords, fill=cor_linha, width=3)

def get_ip(): # <-- NOME CORRIGIDO AQUI
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80)); IP = s.getsockname()[0]; s.close()
    except: IP = "127.0.0.1"
    return IP

def gerar_dashboard():
    conf = carregar_config()
    is_dark = conf.get('dark_mode', True)
    fiat = conf['fiat'].upper()
    
    BG = (0, 0, 0) if is_dark else (255, 255, 255)
    TXT = (255, 255, 255) if is_dark else (0, 0, 0)
    SEC = (150, 150, 150) if is_dark else (80, 80, 80)
    
    img = Image.new('RGB', (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)
    fonts = carregar_fontes()
    simbolo = "R$" if fiat == "BRL" else ("€" if fiat == "EUR" else "$")

    # Header
    draw.line((0, 90, WIDTH, 90), fill=TXT, width=2)
    icon = baixar_icone(conf['coin'], is_dark)
    if icon: img.paste(icon, (20, 10))
    
    draw.text((100, 20), CACHE_DADOS['nome_display'], font=fonts['big'], fill=TXT)
    draw.text((100, 60), CACHE_DADOS['simbolo_display'], font=fonts['small'], fill=SEC)

    val_max = CACHE_DADOS['high']
    val_min = CACHE_DADOS['low']
    fmt_h = f"{val_max:,.2f}" if val_max >= 0.01 else f"{val_max:.8f}"
    fmt_l = f"{val_min:,.2f}" if val_min >= 0.01 else f"{val_min:.8f}"
    txt_max = f"▲ {simbolo}{fmt_h}"
    txt_min = f"▼ {simbolo}{fmt_l}"
    
    draw.text((380, 25), txt_max, font=fonts['small'], fill=SEC)
    draw.text((380, 55), txt_min, font=fonts['small'], fill=SEC)

    # Relógio
    hora = datetime.now().strftime("%H:%M")
    w_hora = draw.textlength(hora, font=fonts['big'])
    pos_hora_x = WIDTH - 80 - 20 - w_hora
    draw.text((pos_hora_x, 25), hora, font=fonts['big'], fill=TXT)

    # Preço
    p_val = CACHE_DADOS['preco']
    if p_val < 0.0001: preco_str = f"{simbolo} {p_val:.8f}"
    elif p_val < 1.0: preco_str = f"{simbolo} {p_val:.6f}"
    else: preco_str = f"{simbolo} {p_val:,.2f}"
    
    fonte_preco = fonts['huge']
    w_p = draw.textlength(preco_str, font=fonte_preco)
    if w_p > (WIDTH - 40):
        fonte_preco = fonts['large']
        w_p = draw.textlength(preco_str, font=fonte_preco)
    
    draw.text(((WIDTH - w_p)/2, 120), preco_str, font=fonte_preco, fill=TXT)

    # Variação
    change = CACHE_DADOS['change']
    sinal = "▲" if change >= 0 else "▼"
    var_txt = f"{sinal} {abs(change):.2f}%"
    w_v = draw.textlength(var_txt, font=fonts['big'])
    draw.text(((WIDTH - w_v)/2, 210), var_txt, font=fonts['big'], fill=TXT)

    # Cotação Invertida
    cotacao_str = ""
    usd = CACHE_DADOS.get('usd_brl', 0)
    if usd > 0:
        if fiat == 'BRL': cotacao_str = f"1 BRL = $ {(1/usd):.3f}"
        elif fiat == 'USD': cotacao_str = f"1 USD = R$ {usd:.3f}"
        else: cotacao_str = f"USD/BRL: {usd:.3f}"
    
    if cotacao_str:
        w_c = draw.textlength(cotacao_str, font=fonts['med'])
        draw.text(((WIDTH - w_c)/2, 260), cotacao_str, font=fonts['med'], fill=SEC)

    # Gráfico
    if CACHE_DADOS['historico']:
        desenhar_grafico_manual(draw, CACHE_DADOS['historico'], (0, 310, WIDTH, 170), TXT)

    # QR Code (CORRIGIDO)
    try:
        ip = get_ip() # Chama a função com o nome correto
        url = f"http://{ip}:5000"
        qr = qrcode.QRCode(box_size=1, border=1)
        qr.add_data(url); qr.make(fit=True)
        fill = "white" if is_dark else "black"
        back = "black" if is_dark else "white"
        
        # Converte para RGB para evitar erro de paleta ao colar
        qr_img = qr.make_image(fill_color=fill, back_color=back).convert('RGB')
        qr_img = qr_img.resize((70, 70), Image.NEAREST)
        
        # Cola no canto superior direito
        img.paste(qr_img, (WIDTH - 85, 10))
    except Exception as e:
        print(f"[ERRO QR] {e}")

    return img

def atualizar_hardware():
    STATUS["msg"] = "Gerando imagem..."
    img = gerar_dashboard()
    img.save("static_preview.png")
    STATUS["imagem_pronta"] = True
    STATUS["msg"] = "Site atualizado."
    
    if HAS_SCREEN:
        if screen_lock.acquire(blocking=False):
            try:
                STATUS["msg"] = "Atualizando E-Ink..."
                print("[E-INK] Atualizando...")
                epd = epd_driver.EPD()
                epd.init()
                img_bw = img.convert('1', dither=Image.FLOYDSTEINBERG)
                epd.display(epd.getbuffer(img_bw))
                epd.sleep()
                print("[E-INK] Concluído.")
                STATUS["msg"] = "Tela OK."
            except Exception as e: print(f"Erro HW: {e}")
            finally: screen_lock.release()

def atualizar_tudo(force=False):
    global STATUS
    if STATUS["ocupado"] and not force: return
    STATUS["ocupado"] = True
    if atualizar_dados(force): atualizar_hardware()
    STATUS["ocupado"] = False

def loop_principal():
    print("--- APP CRIPTO INICIADO ---")
    atualizar_tudo(force=True)
    while True:
        conf = carregar_config()
        agora = time.time()
        # Lê o intervalo da configuração
        if (agora - CACHE_DADOS['last_update']) > conf.get('intervalo', 300):
            print("[AUTO] Atualizando...")
            atualizar_tudo()
        time.sleep(5)

# ============================================================================
# INTERFACE WEB (LAYOUT PC/HORIZONTAL)
# ============================================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>E-ink + Cripto</title>
    <style>
        :root {
            --bg-color: #f0f2f5; --text-color: #333; --card-bg: #ffffff;
            --card-border: #ddd; --input-bg: #fff; --input-border: #ccc;
            --input-text: #333; --coin-bg: #f8f9fa; --coin-active-bg: #fff;
            --status-text: #666; --accent: #FCD535;
        }

        body.dark {
            --bg-color: #1a1a1a; --text-color: #f0f0f0; --card-bg: #2d2d2d;
            --card-border: #444; --input-bg: #444; --input-border: #555;
            --input-text: #fff; --coin-bg: #333; --coin-active-bg: #222;
            --status-text: #aaa;
        }
        
        body { 
            background-color: var(--bg-color); color: var(--text-color); 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0; padding: 20px; transition: 0.3s;
        }

        .container { max-width: 1200px; margin: 0 auto; }
        
        .header-row {
            display: flex; justify-content: space-between; align-items: center; 
            margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid var(--card-border);
        }
        h2 { margin: 0; color: var(--accent); }
        
        /* LAYOUT HORIZONTAL (GRID) */
        .layout-grid {
            display: grid; 
            grid-template-columns: 1fr 1fr; /* Duas colunas iguais */
            gap: 20px;
            align-items: start;
        }

        .card { 
            background: var(--card-bg); padding: 20px; border-radius: 12px; 
            border: 1px solid var(--card-border); box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            margin-bottom: 20px;
        }

        /* Preview na Coluna Esquerda */
        img.preview { width: 100%; border-radius: 8px; border: 1px solid var(--card-border); display: block; }
        
        .status-bar { 
            display: flex; justify-content: space-between; font-size: 0.85em; 
            color: var(--status-text); margin-top: 8px; font-weight: 500;
        }
        
        /* Configurações na Coluna Direita */
        h3 { margin-top: 0; margin-bottom: 15px; border-bottom: 1px solid var(--card-border); padding-bottom: 10px; font-size: 1.1em;}
        
        .coin-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 15px; }
        .coin-btn { 
            background: var(--coin-bg); padding: 10px; text-align: center; border-radius: 8px; 
            cursor: pointer; border: 1px solid var(--card-border); font-weight: 500; transition: 0.2s; font-size: 0.9em;
        }
        .coin-btn:hover { border-color: var(--accent); }
        .coin-btn.active { border-color: var(--accent); color: var(--accent); background: var(--coin-active-bg); font-weight: bold;}
        
        select, input { 
            width: 100%; padding: 10px; margin-bottom: 10px; 
            background: var(--input-bg); border: 1px solid var(--input-border); 
            color: var(--input-text); border-radius: 8px; font-size: 16px; box-sizing: border-box;
        }
        label { display: block; margin-bottom: 5px; font-size: 0.9em; opacity: 0.8; }
        
        button { width: 100%; padding: 12px; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; }
        .btn-update { background: #007bff; color: white; margin-top: 10px;}
        .btn-toggle { background: var(--card-bg); color: var(--text-color); border: 1px solid var(--card-border); padding: 8px 15px; }

        /* Responsividade para Celular */
        @media (max-width: 768px) {
            .layout-grid { grid-template-columns: 1fr; } /* Vira 1 coluna */
            .coin-grid { grid-template-columns: repeat(2, 1fr); }
        }
    </style>
    <script>
        function selectCoin(id) { document.getElementById('coin_input').value = id; document.forms['configForm'].submit(); }
        setInterval(() => {
            document.getElementById('preview').src = '/imagem_preview?' + new Date().getTime();
            fetch('/api/status').then(r=>r.json()).then(d => {
                document.getElementById('status').innerText = d.msg;
                document.getElementById('last_up').innerText = d.last_update_str;
            });
        }, 3000);
    </script>
</head>
<body class="{% if config.dark_mode %}dark{% endif %}">
    <div class="container">
        <!-- CABEÇALHO SITE -->
        <div class="header-row">
            <h2>₿ E-ink + Cripto</h2>
            <div style="display:flex; align-items:center; gap:10px;">
                <span style="font-size:12px; opacity:0.5">{{ ip }}</span>
                <form action="/toggle_mode" method="POST" style="margin:0;">
                    <button class="btn-toggle">{% if config.dark_mode %}☀{% else %}🌙{% endif %}</button>
                </form>
            </div>
        </div>

        <div class="layout-grid">
            
            <!-- COLUNA ESQUERDA: PREVIEW -->
            <div class="col-left">
                <div class="card">
                    <img id="preview" src="/imagem_preview" class="preview">
                    <div class="status-bar">
                        <span id="status">{{ status.msg }}</span>
                        <span id="last_up">{{ status.last_update_str }}</span>
                    </div>
                    <form action="/force_update" method="POST">
                        <button class="btn-update">🔄 Atualizar Tela Agora</button>
                    </form>
                </div>
            </div>

            <!-- COLUNA DIREITA: CONFIGURAÇÃO -->
            <div class="col-right">
                <form id="configForm" action="/salvar" method="POST">
                    <input type="hidden" name="coin" id="coin_input" value="{{ config.coin }}">
                    
                    <div class="card">
                        <h3>Selecionar Ativo</h3>
                        <div class="coin-grid">
                            {% for code, info in cryptos.items() %}
                            <div class="coin-btn {% if config.coin == code %}active{% endif %}" onclick="selectCoin('{{ code }}')">
                                {{ info.nome }}
                            </div>
                            {% endfor %}
                        </div>
                    </div>

                    <div class="card">
                        <h3>Preferências</h3>
                        <label>Moeda Base</label>
                        <select name="fiat" onchange="document.getElementById('configForm').submit()">
                            <option value="BRL" {% if config.fiat == 'BRL' %}selected{% endif %}>Real (BRL)</option>
                            <option value="USD" {% if config.fiat == 'USD' %}selected{% endif %}>Dólar (USD)</option>
                            <option value="EUR" {% if config.fiat == 'EUR' %}selected{% endif %}>Euro (EUR)</option>
                        </select>
                        
                        <label>Intervalo de Atualização (segundos)</label>
                        <input type="number" name="intervalo" value="{{ config.intervalo }}" min="10">
                        
                        <button type="submit" style="background:#28a745; margin-top:10px;">Salvar Preferências</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    conf = carregar_config()
    # Chama get_ip_address() e passa para o template
    return render_template_string(HTML_TEMPLATE, config=conf, cryptos=CRYPTOS, status=STATUS, ip=get_ip())

@app.route('/imagem_preview')
def imagem_preview():
    if os.path.exists("static_preview.png"): return send_file("static_preview.png", mimetype='image/png')
    return "...", 404

@app.route('/api/status')
def api_status(): return jsonify(STATUS)

@app.route('/salvar', methods=['POST'])
def salvar():
    coin = request.form.get('coin')
    curr = request.form.get('fiat')
    
    # Tratamento de erro se o campo vier vazio
    try:
        inter = int(request.form.get('intervalo'))
        if inter < 10: inter = 10 # Mínimo 10s agora
    except: inter = 300
    
    dark = request.form.get('dark') == '1'
    conf = {"coin": coin, "fiat": curr, "intervalo": inter, "dark_mode": dark}
    salvar_config(conf)
    
    threading.Thread(target=lambda: atualizar_tudo(force=True)).start()
    return redirect(url_for('index'))

@app.route('/force_update', methods=['POST'])
def force_update():
    threading.Thread(target=lambda: atualizar_tudo(force=True)).start()
    return redirect(url_for('index'))

@app.route('/toggle_mode', methods=['POST'])
def toggle_mode():
    conf = carregar_config()
    conf['dark_mode'] = not conf.get('dark_mode', False)
    salvar_config(conf)
    threading.Thread(target=atualizar_hardware).start()
    return redirect(url_for('index'))

if __name__ == '__main__':
    t = threading.Thread(target=loop_principal, daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=5000)