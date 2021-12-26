import discord
from discord.ext import tasks
from asyncio import gather
from urllib import request
from xml.etree import ElementTree as ET
from pickle import load, dump
from random import randint

RSS_URL = 'https://feeds.soundcloud.com/users/soundcloud:users:593801271/sounds.rss'

def get_last_episode_from_rss(rss_url):
    response = request.urlopen(rss_url)
    s = response.read()
    tree = ET.fromstring(s)
    return tree.find('channel').find('item')


class EventyrBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner_id = 162645711484223489
        self.bound_channels = {737327854186135652 : 737327854186135656}
        self.subscribed_users = {162645711484223489}
        self.load_state()
        self.last_episode = None

    async def on_ready(self):
        if not self.tick.is_running():
            self.tick.start()

    async def on_message(self, message):
        if message.author == self.user:
            return
        if any(message.content.lower().startswith(f'{roll_word} ') for roll_word in ['rull', 'roll', 'trill']):
            dice_string = message.content[(message.content.find(' ') + 1):].lower()
            result = self.roll(dice_string)
            await message.channel.send(result)
            return
        if message.guild == None:
            return await self.on_direct_message(message)
        if self.user in message.mentions:
            return await self.on_mention_message(message)
    
    async def on_direct_message(self, message):
        print(f'{message.author} says {message.content} to me')
        if any(message.content.lower().startswith(unsubscription_keyword) for unsubscription_keyword in ['unsub', 'unbind', 'stop', 'slutt', 'disable']):
            await self.unsubscribe_user(message.author)
        elif any(message.content.lower().startswith(subscription_keyword) for subscription_keyword in ['sub', 'start', 'følg', 'enable']):
            await self.subscribe_user(message.author)
    
    async def on_mention_message(self, message):
        bot_mention = f'<@!{self.user.id}>'
        raw_message = message.content.replace(bot_mention, '').strip()
        if any(raw_message.lower().startswith(f'{roll_word} ') for roll_word in ['rull', 'roll', 'trill']):
            dice_string = raw_message[(raw_message.find(' ') + 1):].lower()
            result = self.roll(dice_string)
            await message.channel.send(result)
            return
        if message.channel.permissions_for(message.author).administrator:
            self.on_admin_message(message)
        
    async def on_admin_message(self, message):
        triggered = False
        bot_mention = f'<@!{self.user.id}>'
        raw_message = message.content.replace(bot_mention, '').strip()
        if any(unsubscription_keyword in raw_message.lower() for unsubscription_keyword in ['unsub', 'unbind', 'stop', 'slutt', 'disable']):
            await self.unbind_channel(message.channel)
            triggered = True
        elif any(subscription_keyword in raw_message.lower() for subscription_keyword in ['sub', 'bind', 'start', 'følg', 'enable']):
            await self.bind_channel(message.channel)
            triggered = True
        return triggered
    
    def get_last_episode(self):
        response = request.urlopen(RSS_URL)
        s = response.read()
        tree = ET.fromstring(s)
        return tree.find('channel').find('item')
    
    def roll(self, dice_string):
        i = 0
        total = 0
        pieces = []
        unknown_values = []
        sign = 1
        while i < len(dice_string):
            i_plus = dice_string.find('+', i)
            i_plus = len(dice_string) if i_plus == -1 else i_plus
            i_minus = dice_string.find('-', i)
            i_minus = len(dice_string) if i_minus == -1 else i_minus
            i_next = min(i_plus, i_minus)
            current_piece = dice_string[i:i_next].strip().lower()
            is_raw_int = False
            try:
                n = int(current_piece) * sign
                is_raw_int = True
                total += n
                pieces.append(str(n) if n >= 0 else f'({n})')
            except ValueError:
                pass
            is_dice_roll = False
            if not is_raw_int:
                try:
                    is_dice_roll = True
                    d_index = current_piece.find('d')
                    if d_index != -1:
                        dice_count = 1
                        if d_index > 0:
                            dice_count = int(current_piece[:d_index])
                        dice_type = int(current_piece[d_index+1:])
                        for _ in range(dice_count):
                            n = randint(1, dice_type) * sign
                            total += n
                            pieces.append(str(n) if n >= 0 else f'({n})')
                except ValueError:
                    is_dice_roll = False
            
            
            # unknown value:
            if not is_raw_int and not is_dice_roll:
                if sign == 1:
                    unknown_values.append(f'+ {current_piece}')
                    pieces.append(current_piece)
                else:
                    unknown_values.append(f'- {current_piece}')
                    pieces.append(f'(-{current_piece})')
            if i_plus < i_minus:
                sign = 1
            else:
                sign = -1
            i = i_next + 1
        pieces_together = ' + '.join(pieces)
        result = ' '.join([total] + [unknown_values])
        return f'{pieces_together} = {result}'

    @tasks.loop(seconds=30)
    async def tick(self):
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
        self.subscribed_users.add(user.id)
        self.save_state()
        await user.send('Da sier jeg ifra når ny podcast kommer ut! :partying_face:')

    async def unsubscribe_user(self, user):
        self.subscribed_users.remove(user.id)
        self.save_state()
        await user.send('Greit :cry: Hvis du ombestemmer deg, vet du hvor du finner meg')

    async def bind_channel(self, channel):
        self.bound_channels[channel.guild.id] = channel.id
        self.save_state()
        await channel.send('Den er grei - kanalen er notert')

    async def unbind_channel(self, channel):
        del self.bound_channels[channel.guild.id]
        self.save_state()
        await channel.send('Ok, kanalen er nå ~~notert~~ det omvendte av notert')

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