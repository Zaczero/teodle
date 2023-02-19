import os
from asyncio import create_task, sleep
from datetime import datetime
from pathlib import Path

import timeago
from fastapi import FastAPI, Form
from starlette import status
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.websockets import WebSocket, WebSocketDisconnect

from blacklist import Blacklist
from config import BLACKLIST_PATH, CLIPS_PATH, DOWNLOAD_DIR, RANKS_DIR
from downloader import Downloader
from summary import get_summary, update_summary
from twitch_monitor import TwitchMonitor
from vote import Vote, VoteState

app = FastAPI()
app.mount('/static', StaticFiles(directory='static'), name='static')
app.mount(f'/{RANKS_DIR}', StaticFiles(directory=RANKS_DIR), name='ranks')
app.mount(f'/{DOWNLOAD_DIR}', StaticFiles(directory=DOWNLOAD_DIR), name='download')

tmpl = Jinja2Templates(directory='templates')


vote: Vote

twitch_monitor = TwitchMonitor()
downloader = Downloader()


def set_vote(vote_: Vote) -> None:
    global vote
    vote = vote_
    twitch_monitor.load(vote)
    downloader.load(vote)


set_vote(Vote(CLIPS_PATH))


@app.on_event('startup')
async def startup() -> None:
    create_task(downloader.loop())
    create_task(twitch_monitor.loop())


def default_context(request: Request) -> dict:
    return {
        'request': request,
        'css_mtime': int(os.stat('static/css/style.css').st_mtime),
        'vote': vote
    }


def clips_mtime() -> str:
    return timeago.format(datetime.fromtimestamp(CLIPS_PATH.stat().st_mtime),
                          datetime.now())


@app.get('/')
async def index(request: Request):
    ctx = default_context(request)

    if vote.state == VoteState.IDLE:
        return tmpl.TemplateResponse('idle.jinja2', ctx | {
            'config_mtime': clips_mtime(),
            'downloader': downloader
        })

    elif vote.state == VoteState.VOTING:
        return tmpl.TemplateResponse('voting.jinja2', ctx)

    elif vote.state == VoteState.RESULTS:
        return tmpl.TemplateResponse('results.jinja2', ctx | {
            'summary': get_summary() if not vote.has_next_clip else None
        })

    raise Exception('Not implemented vote state')


INDEX_REDIRECT = RedirectResponse('/', status_code=status.HTTP_302_FOUND)


@app.post('/cast_vote')
async def cast_vote(clip_idx: int = Form(), rank: str = Form()):
    # ensure the client state
    if vote.clip_idx == clip_idx and vote.state in {VoteState.VOTING}:
        vote.cast_teo_vote(rank)
        vote.end_clip()

        if not vote.has_next_clip:
            update_summary(vote)

    return INDEX_REDIRECT


@app.post('/next_clip')
async def next_clip(clip_idx: int = Form()):
    global vote

    # ensure the client state
    if vote.clip_idx == clip_idx and vote.state in {VoteState.IDLE, VoteState.RESULTS}:
        if vote.has_next_clip:
            async with twitch_monitor.lock:
                if not twitch_monitor.run_loop.is_set():
                    await twitch_monitor.connect()

            vote.begin_next_clip()

        else:
            async with twitch_monitor.lock:
                await twitch_monitor.disconnect()

            set_vote(Vote(CLIPS_PATH))

    return INDEX_REDIRECT


@app.get('/config')
async def get_config(request: Request):
    if vote.state != VoteState.IDLE:
        return INDEX_REDIRECT

    with open(CLIPS_PATH) as f:
        config = f.read()

    with open(BLACKLIST_PATH) as f:
        blacklist = f.read()

    return tmpl.TemplateResponse('config.jinja2', default_context(request) | {
        'config': config,
        'blacklist': blacklist,
    })


@app.post('/config')
async def post_config(config: str = Form(), blacklist: str = Form(default='')):
    global vote

    if vote.state != VoteState.IDLE:
        raise HTTPException(500, 'Invalid state: voting in progress')

    config = config.strip()
    blacklist = blacklist.strip()

    try:
        # parse the configs to ensure they are valid
        new_blacklist = Blacklist(blacklist)
        new_vote = Vote(config, blacklist=new_blacklist)

        assert len(new_vote.clips), 'No clips found'
    except Exception as e:
        raise HTTPException(500, str(e))

    for path, content in [(CLIPS_PATH, config), (BLACKLIST_PATH, blacklist)]:
        with open(path, 'r+') as f:
            current = f.read().strip()

            # only update the file if the content has changed
            if current.replace('\r', '') != content.replace('\r', ''):
                print(f'[INFO] Saving config: {path}')
                f.seek(0)
                f.write(content)
                f.truncate()

    set_vote(new_vote)

    return INDEX_REDIRECT


@app.websocket('/ws')
async def websocket(ws: WebSocket) -> None:
    await ws.accept()

    try:
        while True:
            await ws.send_json({'total': vote.total_users_votes})
            await sleep(0.2)
            await vote.wait_user_vote()

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await ws.close(1011, str(e))
