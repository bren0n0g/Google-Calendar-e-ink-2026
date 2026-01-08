# **📅 Calendário Inteligente E-Ink com Raspberry Pi**

Um calendário digital de baixo consumo energético que sincroniza com o Google Agenda, mostra a previsão do tempo e permite gestão via interface web local.

*(Substitua este texto pelo link de uma foto real do projeto ou arraste a imagem para a issue do github para gerar um link)*

## **🚀 Funcionalidades**

* **Sincronização Automática:** Atualiza a cada 15 min com o Google Calendar.  
* **Interface Web Local:** Painel de controle acessível pelo navegador (Flask) para adicionar eventos manuais.  
* **Ecrã E-Ink:** Utiliza um display Waveshare 7.5" V2 (baixo consumo e alta visibilidade).  
* **Informações em Tempo Real:** Exibe data, hora e previsão do tempo (via Open-Meteo).  
* **Modo Porta-Retratos:** Permite enviar fotos para serem exibidas no ecrã com dithering automático.  
* **Layout Dinâmico:** Grelha de calendário que se adapta a meses de 4, 5 ou 6 semanas.

## **🛠️ Hardware Utilizado**

* **Raspberry Pi Zero 2 W** (ou qualquer modelo com 40 pinos).  
* **Waveshare 7.5inch E-Ink Display HAT (V2)**.  
* Cartão MicroSD (16GB+).  
* Fonte de Alimentação 5V.

## **⚙️ Instalação e Configuração**

### **1\. Pré-requisitos**

Certifique-se de que o SPI está ativado no Raspberry Pi (sudo raspi-config).

### **2\. Clonar o Repositório**

git clone \[https://github.com/SEU\_USUARIO/calendario-eink.git\](https://github.com/SEU\_USUARIO/calendario-eink.git)  
cd calendario-eink

### **3\. Instalar Dependências**

Recomenda-se usar um ambiente virtual:

python3 \-m venv venv  
source venv/bin/activate  
pip install \-r requirements.txt

### **4\. Configuração do Google Calendar**

1. Crie um projeto no Google Cloud Console.  
2. Ative a API do Google Calendar.  
3. Crie uma Service Account e baixe o JSON.  
4. Renomeie para credentials.json e coloque na pasta raiz do projeto.  
5. Partilhe a sua agenda do Google com o email da Service Account.

### **5\. Executar**

python app.py

O servidor ficará acessível em http://IP-DO-RASPBERRY:5000.

## **📸 Screenshots**

| Calendário | Interface Web |
| :---- | :---- |
|  |  |

## **📝 Licença**

Este projeto está sob a licença MIT. Sinta-se à vontade para usar e modificar.