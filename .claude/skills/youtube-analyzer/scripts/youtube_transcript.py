#!/usr/bin/env python3
"""YouTube 자막/메타데이터 추출 스크립트"""

import sys
import json
import re
import subprocess

def extract_video_id(url):
    """YouTube URL에서 video ID 추출"""
    patterns = [
        r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'(?:embed/)([a-zA-Z0-9_-]{11})',
        r'(?:shorts/)([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_metadata(url):
    """yt-dlp로 메타데이터 추출"""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'yt_dlp',
             '--dump-json', '--no-download', '--no-warnings', url],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                'title': data.get('title', ''),
                'channel': data.get('channel', data.get('uploader', '')),
                'duration': data.get('duration', 0),
                'upload_date': data.get('upload_date', ''),
                'view_count': data.get('view_count', 0),
                'description': data.get('description', '')[:500],
                'tags': data.get('tags', [])[:10],
                'thumbnail': data.get('thumbnail', ''),
            }
    except Exception as e:
        print(f"[WARN] metadata extraction failed: {e}", file=sys.stderr)
    return None

def get_transcript(video_id):
    """youtube-transcript-api v1.x로 자막 추출"""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        ytt = YouTubeTranscriptApi()

        # 한국어 우선, 영어 fallback
        for langs in [['ko', 'en'], ['ko'], ['en']]:
            try:
                transcript = ytt.fetch(video_id, languages=langs)
                return {
                    'language': langs[0],
                    'text': '\n'.join([s.text for s in transcript.snippets]),
                    'entries': [{'start': s.start, 'text': s.text} for s in transcript.snippets]
                }
            except:
                pass

        # 아무 자막이나
        try:
            transcript = ytt.fetch(video_id)
            return {
                'language': 'unknown',
                'text': '\n'.join([s.text for s in transcript.snippets]),
                'entries': [{'start': s.start, 'text': s.text} for s in transcript.snippets]
            }
        except:
            pass

    except Exception as e:
        print(f"[WARN] transcript extraction failed: {e}", file=sys.stderr)
    return None

def format_duration(seconds):
    """초를 HH:MM:SS 형식으로"""
    if not seconds:
        return "알 수 없음"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

def main():
    if len(sys.argv) < 2:
        print("Usage: youtube_transcript.py <youtube_url> [--metadata-only]", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    metadata_only = '--metadata-only' in sys.argv

    video_id = extract_video_id(url)
    if not video_id:
        print(json.dumps({'error': 'Invalid YouTube URL'}))
        sys.exit(1)

    result = {'video_id': video_id, 'url': url}

    # 메타데이터
    meta = get_metadata(url)
    if meta:
        result['metadata'] = meta
        result['metadata']['duration_formatted'] = format_duration(meta.get('duration', 0))

    # 자막
    if not metadata_only:
        transcript = get_transcript(video_id)
        if transcript:
            result['transcript'] = transcript
        else:
            result['transcript'] = None
            result['transcript_error'] = '자막을 찾을 수 없습니다'

    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
