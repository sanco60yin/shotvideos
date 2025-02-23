#!/bin/bash

source /home/yjd/whisper_env/bin/activate

v_file=""

while [ ! -f "$v_file" ]; do
    read -p "Please input video file: " v_file
done

a_file="${v_file}.mp3"
v_sub_file="${v_file}_sub.mp4"
v_srt_file="${v_file}.srt"
v_tr_srt="${v_srt_file}_tr.srt"


if [ ! -f "$a_file" ]; then
    # pick up the audio using ffmpeg
    ffmpeg -i "$v_file" -vn -acodec mp3 "$a_file"
    echo "audio file has been generated: $a_file"
else
    echo "audio file is there: $a_file"
fi


if [ ! -f "$v_srt_file" ]; then
    whisper "$a_file" --model small --language English --output_format srt
    cp $v_srt_file $v_tr_srt
else
    echo "srt file is there: $v_srt_file"
fi

while true; do
    read -p "Please translate the srt file ${v_tr_srt} then enter [yes]: " tr_yes
    if [[ "$tr_yes" == "yes" ]]; then
        break
    fi
done

if [ ! -f "$v_sub_file" ]; then
    ffmpeg -i "$v_file" -vf "subtitles=${v_tr_srt}" -c:a copy "$v_sub_file"
else
    echo "sub video file is there: $v_sub_file"
fi

echo "sub video file done: ${v_sub_file} !!!"
