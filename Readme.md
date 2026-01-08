# **📅 Calendário Inteligente & Porta-Retratos E-Ink (Raspberry Pi Zero 2 W)**

**Um dispositivo IoT de baixo consumo energético que transforma a sua agenda digital numa obra de arte física.**

Este projeto consiste num calendário digital "set-and-forget" que utiliza um ecrã de tinta eletrónica (E-Ink) para exibir eventos do Google Calendar, a previsão do tempo e fotos personalizadas. O sistema é gerido por um Raspberry Pi Zero 2 W e inclui uma interface Web local completa para gestão e controlo.

## **📖 Índice**

1. [Visão Geral e Funcionalidades](https://www.google.com/search?q=%23-vis%C3%A3o-geral-e-funcionalidades)  
2. [Lista de Material (Hardware)](https://www.google.com/search?q=%23-lista-de-material-hardware)  
3. [Montagem Física Crítica](https://www.google.com/search?q=%23-montagem-f%C3%ADsica-cr%C3%ADtica)  
4. [Instalação do Sistema (Do Zero)](https://www.google.com/search?q=%23-instala%C3%A3%C3%A7%C3%A3o-do-sistema-do-zero)  
5. [Instalação de Software e Dependências](https://www.google.com/search?q=%23-instala%C3%A7%C3%A3o-de-software-e-depend%C3%AAncias)  
6. [Configuração do Google Calendar](https://www.google.com/search?q=%23-configura%C3%A7%C3%A3o-do-google-calendar)  
7. [Automatização (Boot Automático)](https://www.google.com/search?q=%23-automatiza%C3%A7%C3%A3o-boot-autom%C3%A1tico)  
8. [🐛 Resolução de Problemas (Troubleshooting)](https://www.google.com/search?q=%23-resolu%C3%A7%C3%A3o-de-problemas-troubleshooting)  
9. [Como Usar](https://www.google.com/search?q=%23-como-usar)

## **🚀 Visão Geral e Funcionalidades**

Diferente de tablets ou monitores LCD, o ecrã E-Ink não emite luz, não cansa a vista e consome energia apenas quando a imagem muda, permitindo que o dispositivo fique ligado meses a fio sem impacto significativo na conta de luz.

### **O que este sistema faz:**

* **Sincronização Automática:** Um "robô" interno verifica o Google Calendar a cada 15 minutos e atualiza o ecrã se houver mudanças.  
* **Interface Web Local (Flask):** Ao acessar o IP do Raspberry Pi no navegador, tem acesso a um painel de controlo completo para adicionar eventos manuais, navegar entre meses, apagar itens e forçar atualizações.  
* **Modo Porta-Retratos:** Permite fazer upload de qualquer foto pelo telemóvel. O sistema converte a imagem automaticamente usando algoritmo de *dithering* (Floyd-Steinberg) para ficar perfeita no ecrã preto e branco.  
* **Grelha Dinâmica Inteligente:** O calendário desenha-se sozinho. Se o mês tiver 4, 5 ou 6 semanas, a grelha ajusta a altura das linhas para ocupar sempre 100% do ecrã, sem deixar espaços em branco.  
* **Dashboard de Tempo:** Exibe a hora atual e a previsão do tempo (temperatura e probabilidade de chuva) via API Open-Meteo.  
* **QR Code Dinâmico:** Um QR Code é gerado no canto do ecrã para facilitar o acesso à interface web pelo telemóvel.

## **🛠️ Lista de Material (Hardware)**

Para replicar este projeto, precisará de:

1. **Raspberry Pi Zero 2 W:** A versão "2" é essencial. O processador Quad-Core é necessário para renderizar as imagens em Python rapidamente.  
2. **Ecrã E-Ink Waveshare 7.5" HAT (Versão V2):** Resolução 800x480. A versão V2 é a mais comum atualmente.  
3. **Cartão MicroSD:** Mínimo 16GB (Classe 10 / A1 recomendada para não travar o sistema durante atualizações).  
4. **Fonte de Alimentação:** 5V Micro-USB (um carregador de telemóvel antigo de qualidade serve).  
5. **Adaptador Mini-HDMI (Opcional):** Apenas para debug inicial na TV caso a rede falhe.

## **⚠️ Montagem Física Crítica**

Muitos problemas ocorrem aqui. Siga à risca:

1. **Interruptores do HAT (Placa Azul):**  
   * **Display Config:** Deve estar na posição **B**.  
   * **Interface Config:** Deve estar na posição **0**.  
2. **Cabo Flat (Laranja):**  
   * Abra a trava preta do conector levantando-a levemente.  
   * Insira o cabo com o **LADO AZUL VIRADO PARA CIMA** (para o lado da trava).  
   * Empurre até o fim e feche a trava. Se ficar frouxo, o ecrã não liga.  
3. **Encaixe no Pi:**  
   * Pressione o HAT firmemente sobre os 40 pinos do Raspberry Pi. O mau contacto aqui causa o erro "e-Paper busy".

## **💿 Instalação do Sistema (Do Zero)**

Utilizamos uma configuração "Headless" (sem monitor e teclado), tudo via Wi-Fi.

### **1\. Gravar o Sistema Operativo**

Use o **Raspberry Pi Imager** no seu PC:

1. Escolha o OS: **Raspberry** Pi OS **Lite (64-bit)**.  
2. Clique na **Engrenagem (Configurações Avançadas)** antes de gravar:  
   * Defina o Hostname: pi-zero.  
   * Ative o **SSH** (Use password authentication).  
   * Configure o **Wi-Fi** (Nome da rede e Senha). **Atenção:** O Pi Zero 2 W só conecta em redes 2.4GHz.  
   * Defina um Utilizador e Senha (ex: seu-usuario / suasenha).

### **2\. Primeiro Acesso**

1. Insira o cartão e ligue o Pi à tomada. Aguarde 2 minutos.  
2. No PC, abra o terminal e digite: ssh seu-usuario@pi-zero.local.  
   * *Se não encontrar:* Use uma app como **Fing** no telemóvel para descobrir o IP (ex: 10.0.0.XX) e use ssh seu-usuario@SEU-IP.

### **3\. Configuração de Rede (IP Fixo)**

Para evitar que o IP mude e o site pare de funcionar, fixe o IP:

1. Edite: sudo nano /etc/dhcpcd.conf  
2. Adicione no final:  
   interface wlan0  
   static ip\_address=SEU-IP-FIXO/24  \<-- Ex: 10.0.0.200/24  
   static routers=IP-ROTEADOR        \<-- Ex: 10.0.0.1  
   static domain\_name\_servers=8.8.8.8

3. Salve (Ctrl+O, Enter) e Saia (Ctrl+X).

## **📦 Instalação de Software e Dependências**

O Raspberry Pi OS Lite vem "limpo". Precisamos instalar compiladores e bibliotecas manualmente.

### **1\. Ferramentas de Sistema (Obrigatório)**

Execute este bloco para instalar o Git, ferramentas de compilação Python e bibliotecas gráficas e de GPIO:

sudo apt update && sudo apt upgrade \-y  
sudo apt install git python3-dev python3-setuptools python3-venv libjpeg-dev zlib1g-dev liblgpio-dev swig fbi fonts-dejavu \-y

*Nota: liblgpio-dev e swig são cruciais para evitar erros na instalação do gpiozero mais tarde.*

### **2\. Ativar SPI**

O ecrã usa SPI, que vem desligado por padrão.

1. sudo raspi-config  
2. **Interface Options** \-\> **SPI** \-\> **Yes**.  
3. Reinicie: sudo reboot.

### **3\. Ambiente Virtual Python (VENV)**

Para evitar o erro externally-managed-environment no Raspberry Pi Bookworm, usamos um ambiente virtual (venv).

python3 \-m venv venv  
source venv/bin/activate

### **4\. Instalar Bibliotecas Python**

Com o (venv) ativo:

\# Bibliotecas do Projeto  
pip install flask pillow requests qrcode

\# Bibliotecas do Google  
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2

\# Drivers de Hardware  
pip install RPi.GPIO spidev gpiozero lgpio

### **5\. Instalação Manual do Driver Waveshare**

A instalação via pip do driver oficial apresentou problemas de caminhos. A solução robusta é clonar o repositório e mover a biblioteca manualmente.

cd \~  
\# Baixar repositório  
git clone \[https://github.com/waveshare/e-Paper\](https://github.com/waveshare/e-Paper)

\# Copiar APENAS a pasta da biblioteca para a raiz do seu projeto  
cp \-r e-Paper/RaspberryPi\_JetsonNano/python/lib/waveshare\_epd .

\# Limpar o resto para poupar espaço  
rm \-rf e-Paper

*Agora deve ter uma pasta waveshare\_epd azul junto com seus arquivos.*

## **☁️ Configuração do Google Calendar**

Para o calendário funcionar, ele precisa de permissão para ler sua agenda.

1. Acesse o **Google Cloud Console**.  
2. Crie um projeto e ative a **Google Calendar API**.  
3. Crie uma **Service Account** (Conta de Serviço).  
4. Crie uma chave JSON para essa conta e baixe o arquivo.  
5. Renomeie o arquivo para credentials.json e envie para o Raspberry Pi (via scp).  
6. **Passo Crítico:** Abra o arquivo JSON, copie o client\_email e vá na sua Agenda do Google \> Configurações \> Compartilhar \> Adicione esse email com permissão de leitura.

## **🤖 Automatização (Boot Automático)**

Para que o calendário ligue sozinho ao conectar na tomada, criamos um serviço systemd.

1. Crie o arquivo: sudo nano /etc/systemd/system/calendario.service  
2. Cole o conteúdo (ajuste o caminho /home/seu-usuario conforme necessário):

\[Unit\]  
Description=Calendario E-Ink  
After=network-online.target  
Wants=network-online.target

\[Service\]  
User=root  
WorkingDirectory=/home/seu-usuario  
\# AGUARDA INTERNET: Tenta pingar o google antes de iniciar o script  
ExecStartPre=/bin/sh \-c 'until ping \-c1 google.com; do sleep 1; done;'  
ExecStart=/home/seu-usuario/venv/bin/python /home/seu-usuario/app.py  
Restart=always  
RestartSec=10  
Environment=DISPLAY=:0

\[Install\]  
WantedBy=multi-user.target

3. Ative: sudo systemctl enable calendario.service

## **🐛 Resolução de Problemas (Troubleshooting)**

Durante o desenvolvimento, encontramos e resolvemos os seguintes erros comuns:

### **1\. Erro: lgpio.error: 'GPIO busy'**

* **Sintoma:** Ao tentar rodar python app.py manualmente, aparece este erro.  
* **Causa:** O serviço automático (systemd) já está rodando em segundo plano e ocupando os pinos do ecrã.  
* **Solução:** Parar o robô antes de testar manualmente: sudo systemctl stop calendario.service.

### **2\. Erro: fatal error: Python.h: No such file ou command 'swig' failed**

* **Sintoma:** Erro vermelho gigante ao tentar dar pip install gpiozero ou RPi.GPIO.  
* **Causa:** O sistema Lite não tem ferramentas de compilação C/C++.  
* **Solução:** Instalar os headers: sudo apt install python3-dev swig liblgpio-dev.

### **3\. Erro: \[Errno 2\] No such file or directory (Ao iniciar o ecrã)**

* **Sintoma:** O código roda, baixa o clima, mas falha na hora de desenhar.  
* **Causa:** A interface SPI está desligada na BIOS do Raspberry.  
* **Solução:** Rodar sudo raspi-config e ativar o SPI.

### **4\. Problema: Cor preta muito clara/acinzentada**

* **Sintoma:** O texto parece desbotado.  
* **Causa:** Acúmulo de carga ou driver incorreto.  
* **Solução:**  
  1. No código, usamos epd.Clear() para forçar uma limpeza completa (piscar) a cada atualização.  
  2. Alteramos a conversão de imagem para dither=Image.NONE (para texto nítido) ou FLOYDSTEINBERG (para fotos).  
  3. Verificar se o cabo flat está bem encaixado.

### **5\. Problema: Permission denied: 'foto\_custom.png'**

* **Sintoma:** O site dá erro 500 ao tentar fazer upload de foto.  
* **Causa:** O script automático rodou como root e criou o arquivo. O utilizador normal não consegue sobrescrever.  
* **Solução:** Apagar o arquivo travado: sudo rm foto\_custom.png e dar permissões à pasta sudo chown \-R seu-usuario:seu-usuario /home/seu-usuario.

## **📱 Como Usar**

1. **Ligar:** Conecte o Raspberry Pi à tomada. Aguarde \~1 minuto. O ecrã piscará e mostrará o calendário.  
2. **Acessar o Painel:**  
   * Aponte a câmara do telemóvel para o **QR Code** no canto superior direito do ecrã.  
   * Ou digite o IP fixo no navegador (ex: http://SEU-IP-FIXO:5000).  
3. **Funcionalidades do Site:**  
   * **Adicionar Evento:** Digite data, hora e descrição. (Marque "Dia Todo" para eventos sem hora).  
   * **Porta-Retratos:** Envie uma foto da galeria para exibir no ecrã.  
   * **Sincronizar:** Force uma atualização imediata do Google Agenda.

**Autor do Projeto:** \[Seu Nome\]

**Licença:** MIT
