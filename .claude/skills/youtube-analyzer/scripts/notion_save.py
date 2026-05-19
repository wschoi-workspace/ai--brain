#!/usr/bin/env python3
"""YouTube 분석 결과를 Notion DB에 저장"""

import sys
import json
import os
import requests

NOTION_TOKEN = os.environ.get('NOTION_TOKEN', '')
YOUTUBE_DB_ID = '32b4703a-5867-81bc-836d-f3a4f76a0c60'
NOTION_API = 'https://api.notion.com/v1'
HEADERS = {
    'Authorization': f'Bearer {NOTION_TOKEN}',
    'Content-Type': 'application/json',
    'Notion-Version': '2022-06-28'
}

def truncate(text, max_len=2000):
    """Notion rich_text 제한 (2000자)"""
    if not text:
        return ''
    return text[:max_len]

def create_page(data):
    """Notion DB에 페이지 생성"""
    properties = {
        '영상 제목': {
            'title': [{'text': {'content': truncate(data.get('title', '제목 없음'), 200)}}]
        },
        'URL': {'url': data.get('url', '')},
        '채널명': {
            'rich_text': [{'text': {'content': truncate(data.get('channel', ''), 200)}}]
        },
        '핵심 요약': {
            'rich_text': [{'text': {'content': truncate(data.get('summary', ''))}}]
        },
        '주요 인사이트': {
            'rich_text': [{'text': {'content': truncate(data.get('insights', ''))}}]
        },
        '실행 아이디어': {
            'rich_text': [{'text': {'content': truncate(data.get('actions', ''))}}]
        },
        '영상 길이': {
            'rich_text': [{'text': {'content': data.get('duration', '')}}]
        },
        '상태': {'select': {'name': '요약 완료'}},
        '등록일': {'date': {'start': data.get('date', '')}},
    }

    if data.get('category'):
        properties['카테고리'] = {'select': {'name': data['category']}}

    if data.get('rating'):
        properties['유용도'] = {'select': {'name': data['rating']}}

    if data.get('tags'):
        properties['태그'] = {
            'multi_select': [{'name': t[:100]} for t in data['tags'][:5]]
        }

    # 페이지 본문 블록
    children = []

    if data.get('summary_detail'):
        children.append({
            'object': 'block', 'type': 'heading_2',
            'heading_2': {'rich_text': [{'text': {'content': '핵심 요약'}}]}
        })
        for paragraph in data['summary_detail'].split('\n\n'):
            if paragraph.strip():
                children.append({
                    'object': 'block', 'type': 'paragraph',
                    'paragraph': {'rich_text': [{'text': {'content': truncate(paragraph.strip())}}]}
                })

    if data.get('insights_detail'):
        children.append({
            'object': 'block', 'type': 'heading_2',
            'heading_2': {'rich_text': [{'text': {'content': '주요 인사이트'}}]}
        })
        for line in data['insights_detail'].split('\n'):
            if line.strip():
                children.append({
                    'object': 'block', 'type': 'bulleted_list_item',
                    'bulleted_list_item': {'rich_text': [{'text': {'content': truncate(line.strip().lstrip('- '))}}]}
                })

    if data.get('actions_detail'):
        children.append({
            'object': 'block', 'type': 'heading_2',
            'heading_2': {'rich_text': [{'text': {'content': '실행 아이디어'}}]}
        })
        for line in data['actions_detail'].split('\n'):
            if line.strip():
                children.append({
                    'object': 'block', 'type': 'numbered_list_item',
                    'numbered_list_item': {'rich_text': [{'text': {'content': truncate(line.strip().lstrip('0123456789. '))}}]}
                })

    payload = {
        'parent': {'database_id': YOUTUBE_DB_ID},
        'properties': properties,
    }
    if children:
        payload['children'] = children[:100]  # Notion limit

    resp = requests.post(f'{NOTION_API}/pages', headers=HEADERS, json=payload)
    result = resp.json()

    if resp.status_code == 200:
        print(json.dumps({
            'success': True,
            'page_id': result['id'],
            'url': result['url']
        }, ensure_ascii=False))
    else:
        print(json.dumps({
            'success': False,
            'error': result.get('message', str(result))
        }, ensure_ascii=False))
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: notion_save.py '<json_data>'", file=sys.stderr)
        sys.exit(1)

    data = json.loads(sys.argv[1])
    create_page(data)

if __name__ == '__main__':
    main()
