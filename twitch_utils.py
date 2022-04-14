from requests import get

def is_live(channel_name):
    res = get(f'https://www.twitch.tv/{channel_name}')
    content = res.content.decode('utf-8')
    return 'isLiveBroadcast' in content