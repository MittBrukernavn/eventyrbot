import discord
from discord.ext import tasks
from asyncio import gather
from urllib import request
from xml.etree import ElementTree as ET
from pickle import load, dump

RSS_URL = 'https://feeds.soundcloud.com/users/soundcloud:users:593801271/sounds.rss'

def get_last_episode_from_rss(rss_url):
    response = request.urlopen(rss_url)
    s = response.read()
    tree = ET.fromstring(s)
    return tree.find('channel').find('item')


class EventyrBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bound_channels = {737327854186135652 : 737327854186135656}
        self.subscribed_users = {162645711484223489}
        self.load_state()
        self.last_episode = None
        self.has_notified = False

    async def on_ready(self):
        if not self.tick.is_running():
            self.tick.start()

    async def on_message(self, message):
        if message.author == self.user:
            return
        if message.guild == None:
            return await self.on_direct_message(message)
        if self.user in message.mentions:
            return await self.on_mention_message(message)
    
    async def on_direct_message(self, message):
        print(f'{message.author} says {message.content} to me')
        if any(unsubscription_keyword in message.content for unsubscription_keyword in ['unsub', 'stop', 'slutt', 'disable']):
            await self.unsubscribe_user(message.author)
        elif any(subscription_keyword in message.content for subscription_keyword in ['sub', 'start', 'følg', 'enable']):
            await self.subscribe_user(message.author)
    
    async def on_mention_message(self, message):
        bot_mention = f'<@!{self.user.id}>'
        raw_message = message.content.replace(bot_mention, '').strip()
        if not message.channel.permissions_for(message.author).administrator:
            return
        if any(unsubscription_keyword in raw_message.lower() for unsubscription_keyword in ['unsub', 'unbind', 'stop', 'slutt', 'disable']):
            await self.unbind_channel(message.channel)
        elif any(subscription_keyword in raw_message.lower() for subscription_keyword in ['sub', 'bind', 'start', 'følg', 'enable']):
            await self.bind_channel(message.channel)

    def get_last_episode(self):
        response = request.urlopen(RSS_URL)
        s = response.read()
        tree = ET.fromstring(s)
        return tree.find('channel').find('item')

    @tasks.loop(seconds=30)
    async def tick(self):
        if not self.has_notified:
            # notify that bot is online
            await self.notify_all('Bot is now online')
            self.has_notified = True
        try:
            last_episode = self.get_last_episode()
            assert (last_episode is not None)
        except Exception as e:
            print('Failed to get last episode from RSS feed.')
            print(e.message)
            return
        
        # first run:
        if self.last_episode is None:
            self.last_episode = last_episode
            return
        # no new episodes:
        if last_episode.find('guid').text == self.last_episode.find('guid').text:
            return

        # no edge case triggered; new episode found
        self.last_episode = last_episode
        title = last_episode.find('title').text
        link = last_episode.find('link').text
        update = f'Ny episode ute nå! {title}. Hør på {link}, eller der du hører podcast.'
        await self.notify_all(update)
        
    async def send_to_user_id(self, user_id, message):
        user = await self.fetch_user(user_id)
        return await user.send(message)

    async def notify_all(self, msg):
        print(f'Sending "{msg}" to all bound channels')
        channel_messages = [self.get_channel(channel).send(msg) for channel in self.bound_channels.values()]
        user_messages = [self.send_to_user_id(user_id, msg) for user_id in self.subscribed_users]
        await gather(*(channel_messages + user_messages))
    

    async def subscribe_user(self, user):
        await user.send('Subscribing you to eventyrbot updates.')
        self.subscribed_users.add(user.id)
        self.save_state()

    async def unsubscribe_user(self, user):
        await user.send('You will no longer updates from eventyrbot.')
        self.subscribed_users.remove(user.id)
        self.save_state()

    async def bind_channel(self, channel):
        self.bound_channels[channel.guild.id] = channel.id
        self.save_state()

    async def unbind_channel(self, channel):
        del self.bound_channels[channel.guild.id]
        self.save_state()

    def save_state(self):
        with open('state/state.pickle', 'wb') as f:
            state_dict = {
                'bound_channels': self.bound_channels,
                'subscribed_users': self.subscribed_users,
            }
            dump(state_dict, f)

    def load_state(self):
        try:
            with open('state/state.pickle', 'rb') as f:
                state_dict = load(f)
                self.bound_channels = state_dict['bound_channels']
                self.subscribed_users = state_dict['subscribed_users']
        except Exception as e:
            print('Failed to load state from state.pickle:')
            print(e)

if __name__ == '__main__':
    with open('token.txt', 'r') as f:
        bot_token = f.read()

    client = EventyrBot()
    client.run(bot_token)