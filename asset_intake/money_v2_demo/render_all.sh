set -e
N=$(python3 -c "import json; s=json.load(open('spec.json')); print(int(round(s['duration']*s['fps'])))")
H=$((N/2))
node render.mjs --dist dist --spec spec.json --from 0 --to $H --out part0.mp4 > render0.log 2>&1 &
P0=$!
node render.mjs --dist dist --spec spec.json --from $H --to $N --out part1.mp4 > render1.log 2>&1 &
P1=$!
wait $P0; wait $P1
printf "file 'part0.mp4'\nfile 'part1.mp4'\n" > parts.txt
ffmpeg -v error -y -f concat -safe 0 -i parts.txt -i narration.wav -c:v copy -c:a aac -b:a 160k -shortest v2_demo_claude.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 v2_demo_claude.mp4
