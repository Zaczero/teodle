// ==UserScript==
// @name        Teodle for Twitch
// @namespace   Violentmonkey Scripts
// @match       https://www.twitch.tv/*
// @grant       none
// @version     1.0
// @license     GNU Affero General Public License v3.0
// @author      Zaczero
// @description 2/25/2023, 2:02:17 PM
// @updateURL   https://teodle.monicz.dev/teodle.user.js
// @downloadURL https://teodle.monicz.dev/teodle.user.js
// ==/UserScript==

(() => {

    // utility function to get a cookie by name
    const getCookie = name => {
        // https://stackoverflow.com/a/15724300
        // https://creativecommons.org/licenses/by-sa/4.0/
        const value = `; ${document.cookie}`
        const parts = value.split(`; ${name}=`)
        if (parts.length === 2)
            return parts.pop().split(';').shift()
        return undefined
    }

    // determine username, abort if not logged in
    const username = getCookie('login')

    if (username !== undefined) {
        console.info(`[Teodle] Logged in as ${username}`)
    }
    else {
        console.info('[Teodle] Not logged in, aborting')
        return
    }

    // userscript configuration
    const channelName = 'teosgame'
    const channelBaseUrl = `/${channelName}`
    const minTruncateStars = 11

    const rootHtml = `<div id="teodle-for-twitch" class="teodle-hidden">
        <h3 class="teodle-title">
            <div class="teodle-left">
                Teodle <span>for Twitch</span>
            </div>
            <div class="teodle-right">
                <img src="https://teodle.monicz.dev/static/teo.eb4e117a.webp" alt="">
            </div>
        </h3>
        <h5 class="teodle-score">Your score: <span id="teodle-score-stars"></span> <span id="teodle-score-number">⋯</span></h5>
        <div id="teodle-ranks"></div>
    </div>`

    const rootStyle = `
        .teodle-hidden {
            display: none;
        }

        #teodle-for-twitch {
            padding: 10px 13px 12px;
            border-bottom: 1px solid rgba(128, 128, 128, 0.16);
        }

        .teodle-title {
            display: flex;
            justify-content: space-between;
        }

        .teodle-title img {
            max-height: 1em;
            margin-left: .25em;
        }

        .teodle-title span {
            font-size: 0.75em;
            font-weight: lighter;
        }

        #teodle-score-stars {
            letter-spacing: 1px;
        }

        #teodle-score-number {
            font-size: 1.1em;
            font-weight: bold;
            letter-spacing: .5px;
            opacity: 0.85;
            position: relative;
            top: 0.1em;
        }

        .teodle-rank {
            width: 100%;
            padding: .4em .5em .25em;
            border: 1px solid rgba(128, 128, 128, 0.16);
        }

        .teodle-rank:first-child {
            margin-top: .6em;
        }

        .teodle-rank:not(:last-child) {
            margin-bottom: .3em;
        }

        .teodle-rank img {
            max-height: 1.35em;
            margin-right: 0.2em;
        }

        .teodle-rank span {
            font-size: 1.1em;
            font-weight: 600;
            line-height: 1em;
        }

        .teodle-rank span::before {
            content: '!';
            color: #9146ff;
            font-size: 1.3em;
            font-weight: bold;
            font-style: italic;
            margin-right: 0.11em;
        }

        .teodle-ranks-locked .teodle-rank {
            opacity: 0.6;
            pointer-events: none;
        }

        .teodle-vote {
            opacity: 1 !important;
        }

        .teodle-vote span::after {
            content: '';
            display: inline-block;

            background: #CCA423;
            background-clip: content-box;

            width: 6px;
            height: 6px;

            position: relative;
            top: -2px;

            border-radius: 100%;
            box-shadow: 0 0 0 2px #000000, 0 0 0 3px #CCA423;

            margin-left: 1.3em;
        }

        .teodle-answer {
            opacity: 1 !important;
            border-color: #60935D;
            box-shadow: 0 0 0 1px #FCE658;
        }
    `

    let rootElement = undefined
    let scoreStarsElement = undefined
    let scoreNumberElement = undefined
    let ranksElement = undefined

    // utility function to create an element from html
    const createElementFromHtml = html => {
        const div = document.createElement('div')
        div.innerHTML = html.trim()
        return div.firstChild
    }

    // query .chat-room and inject the root element
    const inject = node => {
        const chatRoom = node.querySelector('.chat-room')

        if (!chatRoom)
            return false

        // prevent repeated inject
        if (chatRoom.querySelector('#teodle-for-twitch'))
            return false

        // css
        document.head.insertAdjacentHTML('beforeend', `<style>${rootStyle}</style>`)

        // html
        rootElement = createElementFromHtml(rootHtml)
        chatRoom.prepend(rootElement)

        scoreStarsElement = rootElement.querySelector('#teodle-score-stars')
        scoreNumberElement = rootElement.querySelector('#teodle-score-number')
        ranksElement = rootElement.querySelector('#teodle-ranks')

        return true
    }

    // inject wrapper which also manages the observer
    const injectObserverWrapper = node => {
        if (inject(node)) {
            observer.disconnect()
            afterObserver()
        }
        // don't warn if the node is the body (early inject attempt)
        else if (node !== document.body) {
            console.warn('[Teodle] Failed to inject')
            console.log(node)
        }
    }

    // wait for the chat to load
    const observer = new MutationObserver(mutations => {
        for (const mutation of mutations) {
            for (const node of mutation.addedNodes) {

                // check if the node's direct child contains the .stream-chat class (fast check)
                if (node.children && node.children[0] && node.children[0].classList.contains('stream-chat'))
                    injectObserverWrapper(node)

            }
        }
    })

    // listen for url changes and manage the websocket connection
    const afterObserver = () => {
        window.history.pushState = new Proxy(window.history.pushState, {
            apply: (target, thisObj, args) => {

                if (args.length > 2) {
                    const currentPath = document.location.pathname
                    const newPath = args[2]

                    if (currentPath !== channelBaseUrl && newPath === channelBaseUrl)
                        connect()
                    else if (currentPath === channelBaseUrl && newPath !== channelBaseUrl)
                        disconnect()
                }

                return target.apply(thisObj, args)
            }
        })

        console.info('[Teodle] Initialization complete')

        if (document.location.pathname === channelBaseUrl)
            connect()
    }

    observer.observe(document.body, {
        childList: true,
        subtree: true
    })

    // websocket
    const max_reconnect_interval = 15000
    const init_reconnect_interval = 1000
    const jitter_reconnect_interval = 500

    let reconnect_interval = undefined
    let reconnect_timeout = undefined
    let ws = undefined

    const connect = () => {
        // connect without disconnect is unexpected
        if (ws && (ws.readyState === WebSocket.CONNECTING || ws.readyState === WebSocket.OPEN)) {
            console.warn('[Teodle] Already connected')
            return
        }

        // create a new websocket
        ws = new WebSocket('wss://teodle.monicz.dev/ws')
        ws.onopen = onopen
        ws.onmessage = onmessage
        ws.onclose = onclose

        console.info('[Teodle] Connecting...')
    }

    const disconnect = () => {
        if (reconnect_interval !== undefined)
            clearTimeout(reconnect_timeout)

        ws.close()
        ws = undefined

        reconnect_interval = undefined
        rootElement.classList.add('teodle-hidden')
        console.info('[Teodle] Disconnected')
    }

    const onopen = e => {
        console.info('[Teodle] Exchanging information...')

        ws.send(JSON.stringify({
            'username': username
        }))
    }

    const onmessage = async e => {
        if (e.data === 'ok') {
            reconnect_interval = undefined
            console.info('[Teodle] Exchange complete, connected')
            return
        }

        const json = await e.data.text()
        const obj = JSON.parse(json)

        console.log(obj)
        update(obj)
    }

    const onclose = e => {
        console.log(e)

        if (e.code === 1000)
            return

        // exponential reconnect backoff
        if (reconnect_interval)
            reconnect_interval = Math.min(reconnect_interval * 2, max_reconnect_interval)
        else
            reconnect_interval = init_reconnect_interval

        // add some jitter
        reconnect_interval += Math.floor((Math.random() * 2 - 1) * jitter_reconnect_interval)

        // schedule reconnect
        reconnect_timeout = setTimeout(() => {
            connect()
        }, reconnect_interval)

        console.info(`[Teodle] Reconnecting in ${reconnect_interval}ms...`)
    }

    // application logic
    const update = obj => {
        if (obj.clip.vote_state === 0) {
            // IDLE
            rootElement.classList.add('teodle-hidden')
        }
        else if (obj.clip.vote_state === 1) {
            // VOTING
            rootElement.classList.remove('teodle-hidden')

            if (obj.vote && obj.vote.vote)
                ranksElement.classList.add('teodle-ranks-locked')
            else
                ranksElement.classList.remove('teodle-ranks-locked')
        }
        else {
            // RESULTS
            rootElement.classList.remove('teodle-hidden')
            ranksElement.classList.add('teodle-ranks-locked')
        }

        // update score component
        let newScoreStarsHtml = undefined
        let newScoreNumberHtml = undefined

        if (obj.score) {
            if (obj.score < minTruncateStars)
                newScoreStarsHtml = '⭐️'.repeat(obj.score)
            else
                newScoreStarsHtml = '⭐️ ✕'

            newScoreNumberHtml = obj.score.toString()
        }
        else {
            newScoreStarsHtml = ''
            newScoreNumberHtml = '0';
        }

        scoreStarsElement.innerHTML = newScoreStarsHtml
        scoreNumberElement.innerHTML = newScoreNumberHtml

        // update ranks component
        let newRanksHtml = ''

        for (const [text, filename] of obj.clip.clip_ranks) {
            let extraClasses = ['teodle-rank']

            if (obj.vote && obj.vote.clip_idx === obj.clip.clip_idx && obj.vote.vote === text)
                extraClasses.push('teodle-vote')

            if (obj.clip.clip_answer === text)
                extraClasses.push('teodle-answer')

            newRanksHtml +=
            `<div class="${extraClasses.join(' ')}">
                <img src="https://teodle.monicz.dev/ranks/${filename}" alt="">
                <span>${text}</span>
            </div>`
        }

        ranksElement.innerHTML = newRanksHtml
    }

    // attempt early inject (if the chat is already loaded)
    injectObserverWrapper(document.body)

})()
