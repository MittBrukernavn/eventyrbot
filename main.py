import discord
from discord.ext import tasks
from asyncio import gather
from urllib import request
from xml.etree import ElementTree as ET
from pickle import load, dump
from random import randint

from twitch_utils import is_live

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
        self.songs = {
            'vesper': [
                'Vesper, vesper, vesper en liten kobold-kar',
            ],
            'ork': [
                'En hodeløs ork',
                'Tok seg en snork',
            ]
        }
        self.load_state()
        self.last_episode = None
        self.is_live = True

    async def on_ready(self):
        if not self.tick.is_running():
            self.tick.start()

    async def on_message(self, message):
        if message.author == self.user:
            return
        if message.guild == None:
            return await self.on_direct_message(message)
        if self.user in message.mentions and (await self.on_mention_message(message)):
            return
        if any(message.content.lower().startswith(f'{roll_word} ') for roll_word in ['rull', 'roll', 'trill']):
            dice_string = message.content[(message.content.find(' ') + 1):].lower()
            result = self.roll(dice_string)
            await message.channel.send(result)
            return
        any_misspellings = False
        if any (mathien_misspelling in message.content.lower().split() for mathien_misspelling in ['matien', 'silris', 'sylris', 'xilris']):
            any_misspellings = True
            await message.channel.send('Han heter faktisk Mathien Xyllris :fire:')
        if any(mathien_word in message.content.lower().split() for mathien_word in ['mathien', 'xyllris', 'xylris', 'høyalv', 'druid']):
            await message.channel.send(f'Var det{" forresten" if any_misspellings else ""} noen som sa Mathien Xyllris, høyalv og druid?')
            return
        
    
    async def on_direct_message(self, message):
        print(f'{message.author} says {message.content} to me')
        bot_mention = f'<@!{self.user.id}>'
        raw_message = message.content.replace(bot_mention, '').strip()
        if any(raw_message.lower().startswith(f'{roll_word} ') for roll_word in ['rull', 'roll', 'trill']):
            dice_string = raw_message[(raw_message.find(' ') + 1):].lower()
            result = self.roll(dice_string)
            await message.channel.send(result)
            return True
        if any(message.content.lower().startswith(unsubscription_keyword) for unsubscription_keyword in ['unsub', 'unbind', 'stop', 'slutt', 'disable']):
            await self.unsubscribe_user(message.author)
            return True
        if any(message.content.lower().startswith(subscription_keyword) for subscription_keyword in ['sub', 'start', 'følg', 'enable']):
            await self.subscribe_user(message.author)
            return True
        if message.author.id == self.owner_id:
            if await self.on_owner_message(message):
                return True
        return False
    
    async def on_mention_message(self, message):
        bot_mention = f'<@!{self.user.id}>'
        raw_message = message.content.replace(bot_mention, '').strip()
        if any(raw_message.lower().startswith(f'{roll_word} ') for roll_word in ['rull', 'roll', 'trill']):
            dice_string = raw_message[(raw_message.find(' ') + 1):].lower()
            result = self.roll(dice_string)
            await message.channel.send(result)
            return True
        if message.channel.permissions_for(message.author).administrator:
            await self.on_admin_message(message)
            return True
        return False
        
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
    
    async def on_owner_message(self, message):
        if message.content.startswith('eval '):
            await message.channel.send(eval(message.content[5:]))
            return True
        return False
    
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
                pieces.append('+' if n >= 0 else '-')
                pieces.append(str(abs(n)))
            except ValueError:
                pass
            is_dice_roll = False
            if not is_raw_int:
                try:
                    d_index = current_piece.find('d')
                    if d_index != -1:
                        is_dice_roll = True
                        dice_count = 1
                        if d_index > 0:
                            dice_count = int(current_piece[:d_index])
                        dice_type = int(current_piece[d_index+1:])
                        for _ in range(dice_count):
                            n = randint(1, dice_type) * sign
                            total += n
                            pieces.append('+' if n >= 0 else '-')
                            pieces.append(str(abs(n)))
                except ValueError:
                    is_dice_roll = False
            
            
            # unknown value:
            if not is_raw_int and not is_dice_roll:
                if sign == 1:
                    unknown_values.append(f'+ {current_piece}')
                    pieces.append('+')
                else:
                    unknown_values.append(f'- {current_piece}')
                    pieces.append(f'-')
                pieces.append(str(current_piece))
            if i_plus < i_minus:
                sign = 1
            else:
                sign = -1
            i = i_next + 1
        is_first_positive = len(pieces) >= 1 and pieces[0] == '+'
        pieces_together = ' '.join(pieces[is_first_positive:])
        result = ' '.join([str(total), *unknown_values])
        if pieces_together == result:
            return result
        return f'{pieces_together} = {result}'

    @tasks.loop(minutes=5)
    async def tick(self):
        try:
            was_live = self.is_live
            self.is_live = is_live('eventyrtimen')
            if not was_live and self.is_live:
                await self.send_to_user_id(self.owner_id, 'Eventyrtimen er nå live! https://www.twitch.tv/eventyrtimen')
        except Exception as e:
            print('Failed to get twitch update')
        
        try:
            last_episode = self.get_last_episode()
            assert (last_episode is not None)
        except Exception as e:
            print('Failed to get last episode from RSS feed.')
            print(e)
            try:
                print(e.message)
            except Exception as e:
                print('No message to display')
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

    
    @tick.after_loop
    async def on_tick_cancel(self):
        await self.send_to_user_id(self.owner_id, 'Tick ended - kindly restart it')
    
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