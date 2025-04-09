
import logging
import pytesseract
from PIL import Image
from io import BytesIO
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = '7906468728:AAECtBeI5FCNZkXfpNR8zfKFWb1_M-pfsp8'
ID_GRUPO_AUTORIZADO = -1002548943633

TEMPLATES = {
    'AOVIVO': '🔥 AO VIVO! Odd atual: {X}',
    'PRE': '📊 Pré-jogo com cotação de {X}'
}

LABELS_COTACAO = [
    "Cotações totais",
    "Cotação total",
    "Total de cotações"
]

def extrair_valor_apos_label(imagem: Image.Image):
    texto = pytesseract.image_to_string(imagem, lang='por')
    linhas = texto.splitlines()
    for linha in linhas:
        for label in LABELS_COTACAO:
            if label.lower() in linha.lower():
                partes = linha.split()
                for i, parte in enumerate(partes):
                    if label.split()[0].lower() in parte.lower():
                        try:
                            valor = partes[i+2] if partes[i+1].lower() == 'totais' else partes[i+1]
                            return valor.replace(',', '.')
                        except IndexError:
                            continue
    return None

def processar_mensagem(update: Update, context: CallbackContext):
    message = update.message
    if not message or not message.chat or message.chat.id != ID_GRUPO_AUTORIZADO:
        return

    caption = message.caption or message.text or ""
    palavras = caption.strip().split()
    if not palavras:
        return

    chave = palavras[0].upper()
    if chave not in TEMPLATES:
        return

    if not message.photo:
        message.reply_text("Por favor, envie uma imagem junto com a palavra-chave.")
        return

    foto = message.photo[-1].get_file()
    imagem_bytes = BytesIO()
    foto.download(out=imagem_bytes)
    imagem_bytes.seek(0)
    imagem = Image.open(imagem_bytes)

    valor = extrair_valor_apos_label(imagem)
    if not valor:
        message.reply_text("Não consegui identificar a cotação na imagem.")
        return

    texto_final = TEMPLATES[chave].replace('{X}', valor)

    context.bot.send_photo(
        chat_id=message.chat_id,
        photo=imagem_bytes,
        caption=texto_final
    )

    try:
        context.bot.delete_message(chat_id=message.chat_id, message_id=message.message_id)
    except Exception as e:
        logging.warning(f"Erro ao apagar mensagem: {e}")

def print_chat_id(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    update.message.reply_text(f"Chat ID: `{chat_id}`", parse_mode='Markdown')

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("id", print_chat_id))
    dp.add_handler(MessageHandler(Filters.photo & (Filters.caption | Filters.text), processar_mensagem))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
