import os
import ffmpeg
import whisper
from deep_translator import GoogleTranslator

def segments_to_srt(segments):
    def format_timestamp(seconds):
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hrs:02}:{mins:02}:{secs:02},{millis:03}"

    srt_lines = []

    for i, segment in enumerate(segments, start=1):
        start = format_timestamp(segment['start'])
        end = format_timestamp(segment['end'])
        text = segment['text'].strip()

        srt_lines.append(f"{i}")
        srt_lines.append(f"{start} --> {end}")
        srt_lines.append(text)
        srt_lines.append("")  # 空行分隔每条字幕

    return "\n".join(srt_lines)



def translate_srt(input_file, output_file, src_lang="en", target_lang="zh-CN"):
    translator = GoogleTranslator(source=src_lang, target=target_lang)

    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    translated_lines = []
    for line in lines:
        if line.strip() == "" or line.strip().isdigit() or "-->" in line:
            # 不翻译序号、时间轴、空行
            translated_lines.append(line)
        else:
            try:
                translated = translator.translate(line.strip())
                translated_nl = '\n'.join([translated[i:i + 12] for i in range(0, len(translated), 12)])
                translated_lines.append(translated_nl + "\n")
            except Exception as e:
                print("ERR: translate failed", e)
                translated_lines.append(line)

    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(translated_lines)

def run_mp4_files(directory):
    model = whisper.load_model("turbo")
    writer = whisper.utils.WriteSRT(directory)
    # traverse the entire directory to find mp4 files
    for file in os.listdir(directory):
        file_lower = file.lower()
        if file_lower.endswith(".mp4") and not file_lower.endswith("_cn.mp4") :
            video_file = directory + file
            org_name = os.path.splitext(file)[0]
            audio_file = directory + org_name + ".mp3"
            srt_file = directory + org_name + ".srt"
            cnsrt_file = directory + org_name + "_CN.srt"
            cnvideo_file = directory + org_name + "_CN.mp4"
            # extract audio from video
            if not os.path.exists(audio_file) :
                ffmpeg.input(video_file).output(audio_file).run()
                if not os.path.exists(audio_file):
                    print(f"ERR: extract {audio_file} failed")
                    break
            # convert audio to srt
            if not os.path.exists(srt_file) :
                rt = model.transcribe(audio_file, fp16=False, language="en")
                with open(srt_file, "w", encoding="utf-8") as f:
                    writer.write_result(rt, f)
                if not os.path.exists(srt_file):
                    print(f"ERR: convert {srt_file} failed.")
                    break
            # translate srt to chinese
            if not os.path.exists(cnsrt_file):
                translate_srt(srt_file, cnsrt_file)
                if not os.path.exists(cnsrt_file):
                    print(f"ERR: convert {cnsrt_file} failed.")
                    break
            while True:
                uInput = input(f"file {cnsrt_file} is OK? ")
                if uInput.strip().lower() == "ok" :
                    break
            # Synthesize video with subtitles
            if not os.path.exists(cnvideo_file):
                try :
                    ffmpeg.input(video_file).output(cnvideo_file, vf=f"subtitles={cnsrt_file}", acodec='copy', map='0').run()
                    if not os.path.exists(cnvideo_file):
                        print(f"ERR: convert {cnvideo_file} failed.")
                        break
                except ffmpeg.Error as e:
                    print(e.stderr)
    return


# 示例调用
directory = r"./simples/"  # 这里换成你的目录路径
run_mp4_files(directory)

