import edge_tts
import asyncio


async def text_to_speech(text, file_name, voice="uz-UZ-MadinaNeural"):
    tts = edge_tts.Communicate(text, voice=voice)
    await tts.save(file_name)

# Matn va chiqish faylini belgilaymiz
text = 'Salom! Bugun yaxshi kun. Hayotingizni yanada yorqin va qiziqarli qilish uchun yangi imkoniyatlar izlang. Har bir kun siz uchun yangi bir boshlanish."Agar matnning maqsadi yoki uslubi haqida qo\'shimcha talablaringiz bo\'lsa, ayting.'
output_file = "uzbek_audio.mp3"

# Ovozga aylantirish jarayonini ishga tushiramiz
#asyncio.run(text_to_speech(text, output_file, voice="uz-UZ-MadinaNeural"))
# save wav file
asyncio.run(text_to_speech(text, output_file, voice="uz-UZ-MadinaNeural"))

print("Audio file has been saved as", output_file)