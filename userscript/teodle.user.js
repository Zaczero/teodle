// ==UserScript==
// @name        Teodle for Twitch
// @description A handy userscript for Twitch.tv which adds some more Teodle integration
// @author      Zaczero
// @version     1.1.2
// @license     GNU Affero General Public License v3.0
// @namespace   Violentmonkey Scripts
// @match       https://www.twitch.tv/*
// @grant       none
// @icon        https://teodle.monicz.dev/hash/teo.eb4e117a.webp
// @updateURL   https://teodle.monicz.dev/teodle.user.js
// @downloadURL https://teodle.monicz.dev/teodle.user.js
// @homepageURL https://teodle.monicz.dev/
// ==/UserScript==

(() => {

    const version = '1.1.2'
    const websocketUrl = `wss://teodle.monicz.dev/ws?version=${version}`
    // const websocketUrl = `wss://teodle-beta.monicz.dev/userscript/ws?version=${version}`

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

    if (username === undefined) {
        console.info('[Teodle] Not logged in to Twitch.tv')
        return
    }

    console.info(`[Teodle] Logged in as ${username}, hello!`)

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
                <img src="https://teodle.monicz.dev/hash/teo.eb4e117a.webp" alt="">
            </div>
        </h3>
        <h5 class="teodle-score">Your score: <span id="teodle-score-stars"></span> <span id="teodle-score-number">⋯</span></h5>
        <div id="teodle-ranks"></div>
        <div id="teodle-sign">
            <img src="https://teodle.monicz.dev/hash/teo_sign.ddda5761.webp" alt="">
            <span id="teodle-sign-text"></span>
        </div>
    </div>`

    const rootStyle = `
        .teodle-hidden {
            display: none;
        }

        #teodle-for-twitch {
            position: relative;
            padding: 10px 13px 12px;
            border-bottom: 1px solid rgba(128, 128, 128, 0.16);
        }

        #teodle-sign {
            position: absolute;
            overflow: hidden;
            top: 18%;
            right: -60%;
            width: 60%;
        }

        #teodle-sign-text {
            position: absolute;
            top: 28%;
            left: 50%;
            transform: translate(-50%, -50%) rotate(3.2deg);
            color: black;
            font-weight: 900;
            font-size: 2em;
            width: 100%;
            text-align: center;
        }

        @keyframes teodle-sign-in {
            0% {
                right: -60%;
                transform: translateY(0);
            }
            16% {
                right: -43%;
                transform: translateY(-10%);
            }
            33% {
                right: -26%;
                transform: translateY(0);
            }
            50% {
                right: -10%;
                transform: translateY(-10%);
            }
            66% {
                right: 7%;
                transform: translateY(0);
            }
            83% {
                right: 24%;
                transform: translateY(-10%);
            }
            100% {
                right: 40%;
                transform: translateY(0);
            }
        }

        @keyframes teodle-sign-rotate {
            0% {
                right: 40%;
                transform: scaleX(1);
            }
            50% {
                right: 40%;
                transform: scaleX(-1);
            }
            100% {
                right: 40%;
                transform: scaleX(1);
            }
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
            padding: .35em .5em .2em;
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
    let signElement = undefined
    let signTextElement = undefined

    // utility function to create an element from html
    const createElementFromHtml = html => {
        const div = document.createElement('div')
        div.innerHTML = html.trim()
        return div.firstChild
    }

    // query selector and inject the root element
    const inject = node => {
        // skip if already injected
        if (rootElement && node.contains(rootElement))
            return false

        const target = node.querySelector('.chat-room__content')
        if (!target) {
            // warn only on specific targets
            if (node !== document.body)
                console.warn('[Teodle] Failed to query selector')

            return false
        }

        // inject css (if missing)
        if (!document.head.querySelector('#teodle-for-twitch-css'))
            document.head.insertAdjacentHTML('beforeend', `<style id="teodle-for-twitch-css">${rootStyle}</style>`)

        // inject html
        rootElement = createElementFromHtml(rootHtml)
        target.prepend(rootElement)

        scoreStarsElement = rootElement.querySelector('#teodle-score-stars')
        scoreNumberElement = rootElement.querySelector('#teodle-score-number')
        ranksElement = rootElement.querySelector('#teodle-ranks')
        signElement = rootElement.querySelector('#teodle-sign')
        signTextElement = rootElement.querySelector('#teodle-sign-text')

        console.info('[Teodle] Injected component')
        return true
    }

    // observe the dom for changes and try to inject
    const observer = new MutationObserver(mutations => {
        // observe only on the channel page
        if (!document.location.pathname.startsWith(channelBaseUrl))
            return

        for (const mutation of mutations) {
            for (const node of mutation.addedNodes) {

                // only specific targets/events for performance
                if (
                    (node.classList && // case: chat reset (e.g., switch streamer)
                        node.classList.contains('stream-chat')) ||
                    (node.children && // case: page load
                        node.children[0] &&
                        node.children[0].classList &&
                        node.children[0].classList.contains('stream-chat'))) {

                    inject(node)
                }

            }
        }
    })

    // utility function to start the observer
    const startMutationObserver = () => {
        observer.observe(document.body, {
            childList: true,
            subtree: true
        })

        // attempt to inject on start (in case the chat is already loaded)
        inject(document.body)

        console.info('[Teodle] Started mutation observer')
    }

    // listen for url changes and manage the websocket
    const startUrlListener = () => {
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

        // check if we are already on the channel page
        if (document.location.pathname === channelBaseUrl)
            connect()
    }

    // utility function to animate the round sign
    let lastAnimateSignRound = undefined
    const animateSign = (round) => {
        // skip if the round is the same
        if (lastAnimateSignRound === round)
            return

        lastAnimateSignRound = round

        // skip the first round animation
        if (round <= 1)
            return

        signTextElement.innerText = `Round ${round}`

        // enter from the right
        signElement.style.animation = 'teodle-sign-in 2.9s ease-in-out forwards'

        setTimeout(() => {
            // rotate
            signElement.style.animation = 'teodle-sign-rotate 1.3s linear forwards'

            setTimeout(() => {
                // exit to the right
                signElement.style.animation = 'teodle-sign-in 3s ease-in-out forwards reverse'

                setTimeout(() => {
                    // reset the animation
                    signElement.style.animation = ''
                }, 3000)
            }, 1300)
        }, 2900)
    }

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
        ws = new WebSocket(websocketUrl)
        ws.onopen = onopen
        ws.onmessage = onmessage
        ws.onclose = onclose

        console.info('[Teodle] Connecting...')
    }

    const disconnect = () => {
        if (reconnect_interval !== undefined)
            clearTimeout(reconnect_timeout)

        ws.close(1000)
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

        // do nothing if normal close
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
        reconnect_timeout = setTimeout(connect, reconnect_interval)

        console.info(`[Teodle] Reconnecting in ${reconnect_interval}ms...`)
    }

    // handle state changes
    const update = obj => {
        if (obj.clip.vote_state === 0) {
            // state: IDLE
            rootElement.classList.add('teodle-hidden')
        }
        else if (obj.clip.vote_state === 1) {
            // state: VOTING
            rootElement.classList.remove('teodle-hidden')

            if (obj.vote && obj.vote.clip_idx === obj.clip.clip_idx)
                ranksElement.classList.add('teodle-ranks-locked')
            else {
                ranksElement.classList.remove('teodle-ranks-locked')
                animateSign(obj.clip.clip_idx + 1)
            }
        }
        else {
            // state: RESULTS
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
            newScoreNumberHtml = '0'
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

    // start everything
    startMutationObserver()
    startUrlListener()

    console.info('[Teodle] Initialization complete')

})()
