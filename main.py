import base64
import os
import traceback
from asyncio import create_task, sleep, Event, Lock
from datetime import datetime
from pathlib import Path
from typing import Optional

import timeago
import websockets
from fastapi import FastAPI, Form
from starlette import status
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import RedirectResponse, FileResponse, Response
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.websockets import WebSocket, WebSocketDisconnect
from websockets.exceptions import ConnectionClosedOK
from websockets.legacy.client import WebSocketClientProtocol

from config import NO_MONITOR, TTV_TOKEN, TTV_USERNAME, TTV_CHANNEL
from vote import Vote, VoteState

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

tmpl = Jinja2Templates(directory="templates")

clips_path = Path('clips.txt')
vote = Vote(clips_path)
vote_event = Event()

socket: Optional[WebSocketClientProtocol] = None
socket_event = Event()
socket_lock = Lock()


# vote.begin_next_clip()
# vote.cast_user_vote(str(random.random()), 'bronze')
# vote.cast_user_vote(str(random.random()), 'bronze')
# vote.cast_user_vote(str(random.random()), 'bronze')
# vote.cast_user_vote(str(random.random()), 'gold')
# vote.cast_user_vote(str(random.random()), 'gold')
# vote.cast_user_vote(str(random.random()), 'diamond')
# vote.cast_user_vote(str(random.random()), 'diamond')
# vote.cast_user_vote(str(random.random()), 'diamond')
# vote.cast_user_vote(str(random.random()), 'diamond')


@app.on_event('startup')
async def startup():
    create_task(ttv_monitor())


# TODO: ttv class
async def ttv_disconnect():
    if NO_MONITOR:
        return

    global socket

    if socket is None:
        return

    socket_event.clear()

    try:
        await socket.close()
    except Exception:
        pass

    socket = None
    print('[TTV] 🔴 Disconnected')


async def ttv_connect():
    if NO_MONITOR:
        return

    global socket

    await ttv_disconnect()

    timeout = 0.5

    while True:
        try:
            socket = await websockets.connect('wss://irc-ws.chat.twitch.tv:443')
            break
        except Exception:
            traceback.print_exc()
            await sleep(timeout)
            timeout = min(timeout * 2, 5)

    socket_event.set()
    print('[TTV] 🟢 Connected')


async def ttv_monitor():
    if NO_MONITOR:
        return

    while True:
        # reset connection if connected
        async with socket_lock:
            if socket_event.is_set():
                await ttv_connect()

        await socket_event.wait()

        print('[TTV] Started monitoring')

        try:
            await socket.send(f'CAP REQ :twitch.tv/membership')
            await socket.send(f'PASS oauth:{TTV_TOKEN}')
            await socket.send(f'NICK {TTV_USERNAME}')
            await socket.send(f'JOIN #{TTV_CHANNEL}')

            while True:
                raw = (await socket.recv()).strip()
                parts = raw.split(' ')

                assert len(parts) >= 2, f'Message contains no spaces: {raw}'

                if parts[0] == 'PING':
                    nonce = ' '.join(parts[1:])
                    await socket.send(f'PONG {nonce}')
                elif parts[1] == 'PRIVMSG' and parts[2] == f'#{TTV_CHANNEL}':
                    username = parts[0].split('!')[0].lstrip(':').lower()
                    message = ' '.join(parts[3:]).lstrip(':').lower()

                    if message.startswith('!'):
                        message = message.lstrip('!').strip()

                        # try multiple formats for better compatibility
                        for new_whitespace in ('', '_'):
                            if vote.cast_user_vote(username, message.replace(' ', new_whitespace)):
                                vote_event.set()
                                break

                elif parts[1] in {'JOIN', 'PART', '353'}:
                    pass
                else:
                    print('[TTV]', raw)

        except ConnectionClosedOK:
            pass
        except Exception:
            traceback.print_exc()
            await sleep(2)

        print('[TTV] Stopped monitoring')


def default_context(request: Request) -> dict:
    return {
        'request': request,
        'css_mtime': int(os.stat('static/css/style.css').st_mtime),
        'vote': vote
    }


def clips_mtime() -> str:
    return timeago.format(datetime.fromtimestamp(clips_path.stat().st_mtime),
                          datetime.now())


@app.get('/')
async def index(request: Request):
    if vote.state == VoteState.IDLE:
        return tmpl.TemplateResponse('idle.jinja2', default_context(request) | {
            'config_mtime': clips_mtime()
        })
    elif vote.state == VoteState.VOTING:
        return tmpl.TemplateResponse('voting.jinja2', default_context(request))
    elif vote.state == VoteState.RESULTS:
        return tmpl.TemplateResponse('results.jinja2', default_context(request))

    raise Exception('Not implemented vote state')


INDEX_REDIRECT = RedirectResponse(app.url_path_for(index.__name__), status_code=status.HTTP_302_FOUND)


@app.post('/cast_vote')
async def cast_vote(clip_idx: int = Form(), rank: str = Form()):
    # ensure the client state
    if vote.clip_idx == clip_idx and vote.state in {VoteState.VOTING}:
        vote.cast_teo_vote(rank)
        vote.end_clip()

    return INDEX_REDIRECT


@app.post('/next_clip')
async def next_clip(clip_idx: int = Form()):
    global vote

    # ensure the client state
    if vote.clip_idx == clip_idx and vote.state in {VoteState.IDLE, VoteState.RESULTS}:
        if vote.has_next_clip:
            async with socket_lock:
                if not socket_event.is_set():
                    await ttv_connect()

            vote.begin_next_clip()

        else:
            async with socket_lock:
                await ttv_disconnect()

            vote = Vote(clips_path)

    return INDEX_REDIRECT


@app.get('/config')
async def get_config(request: Request):
    if vote.state != VoteState.IDLE:
        return INDEX_REDIRECT

    with open(clips_path) as f:
        config = f.read()

    return tmpl.TemplateResponse('config.jinja2', default_context(request) | {
        'config': config
    })


@app.post('/config')
async def post_config(config: str = Form()):
    global vote

    if vote.state != VoteState.IDLE:
        raise HTTPException(500, 'Invalid state: voting in progress')

    config = config.strip()

    try:
        new_vote = Vote(config)
        assert len(new_vote.clips), 'No clips were loaded'
    except Exception as e:
        raise HTTPException(500, str(e))

    with open(clips_path, 'r+') as f:
        current_config = f.read().strip()

        if current_config.replace('\r', '') != config.replace('\r', ''):
            print('[INFO] Saving new configuration')
            f.seek(0)
            f.write(config)
            f.truncate()

    vote = new_vote

    return INDEX_REDIRECT


@app.get('/rank/{raw:path}')
async def rank(raw: str):
    rank_image = next((r.image for r in vote.clip.ranks if r.raw == raw), None)

    if rank_image is None:
        raise HTTPException(404)

    if not rank_image.path.exists():
        # https://stackoverflow.com/questions/6018611/smallest-data-uri-image-possible-for-a-transparent-image
        return Response(base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'),
                        media_type='image/gif')

    return FileResponse(rank_image.path)


@app.websocket('/ws')
async def websocket(ws: WebSocket):
    await ws.accept()

    try:
        while True:
            await ws.send_json({'total': vote.total_users_votes})
            await sleep(0.2)

            await vote_event.wait()
            vote_event.clear()

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await ws.close(1011, str(e))
