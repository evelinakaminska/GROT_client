"""
GROT game command line client.
"""

import argparse
import json
import os.path

from urllib.error import HTTPError
from urllib.request import urlopen, Request

import game


SERVER = 'grot-server.games.stxnext.pl'
TOKEN_FILE = os.path.expanduser('~/.grot_token')

_HELP = {
    'help': 'Help on a specific subcommand',
    'register': 'Register your unique token',
    'new_room': 'Create new game room',
    'remove': 'Remove game room',
    'start': 'Start game',
    'join': 'Join game room and wait for start',
    'results': 'Show game results',
    'play_devel': 'Play one move in loop (development mode)',
    'play_vs_bot': 'Play full game against STX Bot',
}


argparser = argparse.ArgumentParser()
subparsers = argparser.add_subparsers(
    dest='subcmd', help='Available commands',
)


def add_parser(name):
    return subparsers.add_parser(
        name, help=_HELP[name], description=_HELP[name]
    )


parser_help = add_parser('help')
parser_help.add_argument('subcommand')

parser_register = add_parser('register')
parser_register.add_argument('token')

parser_new_room = add_parser('new_room')
parser_new_room.add_argument(
    '--title', required=True,
    help='Room title'
)
parser_new_room.add_argument(
    '--board-size', default=5, required=False, type=int, metavar='X',
    help='GROT board size'
)
parser_new_room.add_argument(
    '--max-players', default=15, required=False, type=int, metavar='X',
    help='Maximum players in the room'
)
parser_new_room.add_argument(
    '--allow-multi', default=False, required=False, action='store_true',
    help='Allow users to connect multiple time with the same token'
)
auto_start_group = parser_new_room.add_mutually_exclusive_group(
    required=False
)
auto_start_group.add_argument(
    '--auto-start', default=5, required=False, type=int, metavar='X',
    help='Automatically start game after X minutes'
)
auto_start_group.add_argument(
    '--no-auto-start', default=False, required=False, action='store_true',
    dest='no_start', help='Game can be started only manually.'
)
auto_restart_group = parser_new_room.add_mutually_exclusive_group(
    required=False
)
auto_restart_group.add_argument(
    '--auto-restart', default=5, required=False, type=int, metavar='X',
    help='Automatically clear results after X minutes'
)
auto_restart_group.add_argument(
    '--no-auto-restart', default=False, required=False, action='store_true',
    dest='no_restart', help='Never restart game, show results forever'
)

parser_remove = add_parser('remove')
parser_remove.add_argument('room_id', help='Room ID')

parser_start = add_parser('start')
parser_start.add_argument('room_id', help='Room ID')

parser_join = add_parser('join')
parser_join.add_argument('room_id', help='Room ID')
parser_join.add_argument(
    '--alias', required=False,
    help='Added to your name displayed on results page.'
)

parser_results = add_parser('results')
parser_results.add_argument('room_id', help='Room ID')

parser_play_devel = add_parser('play_devel')

parser_play_vs_bot = add_parser('play_vs_bot')

argparser.add_argument(
    '--debug', default=False, required=False,
    action='store_true', dest='debug', help='debug flag'
)

args = argparser.parse_args()
subcmd = args.subcmd

if not subcmd:
    argparser.parse_args(['--help'])

elif subcmd == 'help':
    argparser.parse_args([args.subcommand, '--help'])

elif subcmd == 'register':
    with open(TOKEN_FILE, 'w') as f:
        f.write(args.token)
    print('Token have been saved.')

else:
    try:
        with open(TOKEN_FILE) as f:
            token = f.read().strip()
    except IOError:
        token = ''
    if len(token) != 36:
        print("""No token saved.
Sign in to http://{} to get your token.
Use 'python3 client.py save token' before using other commands.
""".format(SERVER))

    if token:
        def new_room(title=None, board_size=5, max_players=15, auto_start=5,
                     auto_restart=5, with_bot=False, allow_multi=False):
            data = {
                'title': title,
                'board_size': board_size,
                'max_players': max_players,
                'auto_start': auto_start,
                'auto_restart': auto_restart,
                'with_bot': with_bot,
                'allow_multi': allow_multi,
                'token': token,
            }
            data = json.dumps(data).encode('utf8')

            try:
                resp = urlopen('http://{}/games'.format(SERVER), data=data)
            except HTTPError as e:
                print(e.read().decode('utf8'))
                raise

            data = json.loads(resp.read().decode('utf8', 'ignore'))
            return data['room_id']

        def start_room(room_id):
            data = json.dumps({'token': token}).encode('utf8')
            resp = urlopen(
                'http://{}/games/{}'.format(SERVER, room_id),
                data=data
            )

        def remove_room(room_id):
            req = Request(
                url='http://{}/games/{}?token={}'.format(
                    SERVER, room_id, token
                ),
                method='DELETE'
            )
            return urlopen(req, timeout=60)

        def show_results(room_id):
            req = Request(
                url='http://{}/games/{}/results/?token={}'.format(
                    SERVER, room_id, token
                ),
                headers = {'Accept': 'application/json'},
            )
            data = json.loads(urlopen(req, timeout=60).read().decode('utf8'))
            for i, player in enumerate(data['players']):
                print('{}. {} - {}'.format(
                    i + 1, player['login'], player['score']))

        if subcmd == 'new_room':
            room_id = new_room(
                title=args.title,
                board_size=args.board_size,
                max_players=args.max_players,
                auto_start=None if args.no_start else args.auto_start,
                auto_restart=None if args.no_restart else args.auto_restart,
                allow_multi=args.allow_multi
            )
            print('New game room_id is {}'.format(room_id))

        elif subcmd == 'remove':
            remove_room(args.room_id)

        elif subcmd == 'start':
            start_room(args.room_id)

        elif subcmd == 'join':
            room_url = 'http://{}/games/{}'.format(SERVER, args.room_id)
            print('Check game results {}'.format(room_url))
            game.play(args.room_id, token, SERVER, args.debug, args.alias)
            show_results(args.room_id)

        elif subcmd == 'results':
            show_results(args.room_id)

        elif subcmd == 'play_devel':
            game.play('000000000000000000000000', token, SERVER, debug=True)

        elif subcmd == 'play_vs_bot':
            room_id = new_room(
                max_players=2,
                auto_start=1,
                auto_restart=None,
                with_bot=True,
            )
            try:
                game.play(room_id, token, SERVER, args.debug)
                show_results(room_id)
            finally:
                remove_room(room_id)
