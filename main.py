import pickle

import telebot
from moviepy.editor import *

import config.loadConfig

# чтение из джсона токена
conf = config.loadConfig.read_conf("config/conf.json")
TOKEN = conf["TOKEN"]

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "ASD")


import os, ffmpeg


def compress_video(video_full_path, output_file_name, target_size):
    # Reference: https://en.wikipedia.org/wiki/Bit_rate#Encoding_bit_rate
    min_audio_bitrate = 32000
    max_audio_bitrate = 256000
    print(video_full_path)
    probe = ffmpeg.probe(video_full_path)
    duration = float(probe['format']['duration'])
    try:
        audio_bitrate = float(next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)['bit_rate'])
    except TypeError:
        audio_bitrate = 0
    target_total_bitrate = (target_size * 1024 * 8) / (1.073741824 * duration)

    if 10 * audio_bitrate > target_total_bitrate:
        audio_bitrate = target_total_bitrate / 10
        if audio_bitrate < min_audio_bitrate < target_total_bitrate:
            audio_bitrate = min_audio_bitrate
        elif audio_bitrate > max_audio_bitrate:
            audio_bitrate = max_audio_bitrate
    video_bitrate = target_total_bitrate - audio_bitrate

    i = ffmpeg.input(video_full_path)
    ffmpeg.output(i, os.devnull,
                  **{'c:v': 'libx264', 'b:v': video_bitrate, 'pass': 1, 'f': 'mp4'}
                  ).overwrite_output().run()
    ffmpeg.output(i, output_file_name,
                  **{'c:v': 'libx264', 'b:v': video_bitrate, 'pass': 2, 'c:a': 'aac', 'b:a': audio_bitrate}
                  ).overwrite_output().run()


@bot.message_handler(content_types=['video'])
def process_video(message):
    try:
        video_file = bot.get_file(message.video.file_id)
        bot.send_message(message.chat.id, "Начал округлять..")
        downloaded_file = bot.download_file(video_file.file_path)
        with open('videos\input_video.mp4', 'wb') as video:
            video.write(downloaded_file)

        # Prеобразование видео в видеокружок
        input_video = VideoFileClip("videos\input_video.mp4")
        w, h = input_video.size
        circle_size = 360
        aspect_ratio = float(w) / float(h)

        if w > h:
            new_w = int(circle_size * aspect_ratio)
            new_h = circle_size
        else:
            new_w = circle_size
            new_h = int(circle_size / aspect_ratio)

        resized_video = input_video.resize((new_w, new_h))

        output_video = resized_video.crop(x_center=resized_video.w / 2, y_center=resized_video.h / 2, width=circle_size,
                                          height=circle_size)
        output_video.write_videofile("videos\output_video.mp4", codec="libx264", audio_codec="aac", bitrate="5M")

        compress_video(r'videos\output_video.mp4', 'videos\compressed_video.mp4', 1 * 1000)
        bot.send_message(message.chat.id, "Сжимаю размер, подожди")

        # Отправка видеокружка в чат
        with open("videos\compressed_video.mp4", "rb") as video:
            bot.send_video_note(chat_id=message.chat.id, duration=int(output_video.duration),
                                length=circle_size, data=open('videos\compressed_video.mp4', 'rb'))
    except telebot.apihelper.ApiTelegramException:
        bot.send_message(message.chat.id,
                         "Файл слишком большой\n🫸                        🫷\nвооооооооот такой, а надо\n🤏🤏🤏\nтакой")


print("работаем")
bot.polling()