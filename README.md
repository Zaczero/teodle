# <img height="24" src="https://github.com/Zaczero/teodle/blob/main/static/teo/favicon-32x32.png?raw=true"> Teodle - Guess the rank!

![GitHub Pipenv locked Python version](https://img.shields.io/github/pipenv/locked/python-version/Zaczero/teodle)
[![GitHub](https://img.shields.io/github/license/Zaczero/teodle)](https://github.com/Zaczero/teodle/blob/main/LICENSE)
[![GitHub Repo stars](https://img.shields.io/github/stars/Zaczero/teodle?style=social)](https://github.com/Zaczero/teodle)

Teodle is a Python-powered website for [Twitch streamer Teo](https://www.twitch.tv/teosgame), to watch game clips submitted by his community and guess the ranks.
The livestream viewers can also participate in the game by casting their votes in the Twitch chat.
The most accurate viewers are displayed on the leaderboard.

## Ranking System

The ranking system in Teodle is primarily based on stars, the more stars, the higher the score.

The rules are simple:

- If you guess the exact rank of a game clip, you get 2 stars.
- If you are 1 rank off, you get 1 star.
- Otherwise, you get no stars.

## Live Participation

Viewers can play along during livestreams by voting in the chat and competing for both accuracy and speed. The leaderboard showcases the top performing viewers.

## Media

### Screenshots

<img width="60%" src="https://github.com/Zaczero/teodle/blob/main/resources/thumbnail2.png?raw=true">

### Twitch VODs

*Updated on 26/03/2023*

- Ep15 https://www.twitch.tv/videos/1764231088?t=00h46m13s (newest)
- Ep14 https://www.twitch.tv/videos/1762126641?t=00h19m28s
- Ep13 https://www.twitch.tv/videos/1757327891?t=00h44m59s

<details>
<summary>Show more</summary>

- Ep12 https://www.twitch.tv/videos/1755443214?t=00h37m45s
- Ep11 https://www.twitch.tv/videos/1748843377?t=00h40m01s
- Ep10 https://www.twitch.tv/videos/1743812126?t=00h11m50s
- Ep9 *miscount*
- Ep8 https://www.twitch.tv/videos/1737987350?t=00h52m29s
- Ep7 https://www.twitch.tv/videos/1729233989?t=00h00m25s
- Ep6 https://www.twitch.tv/videos/1721001903?t=00h37m58s
- Ep5 https://www.twitch.tv/videos/1715086976?t=00h22m27s
- Ep4 https://www.twitch.tv/videos/1714133387?t=00h26m40s
- Ep3.5 https://www.twitch.tv/videos/1712305474?t=00h14m05s
- Ep3 https://www.twitch.tv/videos/1711228781?t=00h23m25s
- Ep2 https://www.twitch.tv/videos/1709156468?t=00h13m20s
</details>

### YouTube Series

*Updated on 26/03/2023*

- Ep14 https://www.youtube.com/watch?v=Jjc5SB1DW2A (newest)
- Ep13 https://www.youtube.com/watch?v=2_D9oiSowj0
- Ep12 https://www.youtube.com/watch?v=RDM4UKYhsYw

<details>
<summary>Show more</summary>

- Ep11 https://www.youtube.com/watch?v=9Yes19lVXvQ
- Ep10 https://www.youtube.com/watch?v=lTmzxbdpzC4
- Ep9 *miscount*
- Ep8 https://www.youtube.com/watch?v=SLw8tRcXaBQ
- Ep7 https://www.youtube.com/watch?v=oI3jhIh2u8M
- Ep6 https://www.youtube.com/watch?v=nLFWqaHy6EM
- Ep5 https://www.youtube.com/watch?v=fU9lOPAeA08
- Ep4 https://www.youtube.com/watch?v=cELkMah_xTM
- Ep3.5 https://www.youtube.com/watch?v=0MjMAeJJ67Q
- Ep3 https://www.youtube.com/watch?v=-RRyqxI9K64
- Ep2 https://www.youtube.com/watch?v=noQXO2jvAcw
</details>

## Deployment

We recommend using Docker for the best experience.

### Docker

1. Install [Docker](https://docs.docker.com/get-docker/)
2. Clone and enter the repository

```sh
git clone https://github.com/Zaczero/teodle && cd teodle
```

3. Rename `.env.example` to `.env` and configure the environment variables

   1. `TTV_TOKEN`: Twitch chat access token, get one [here](https://twitchapps.com/tmi/).
   2. `TTV_USERNAME`: Twitch account's username for the token.
   3. `TTV_CHANNEL`: Twitch channel to listen the chat on.

4. Build the image

```sh
docker build . -t teodle
```

5. Start the container

```docker
docker run --rm --env-file .env -p 8000:8000 -v $(pwd)/data:/app/data teodle
```

6. Access the website at [http://localhost:8000](http://localhost:8000)

## Footer

### Contact

- Email: [kamil@monicz.pl](mailto:kamil@monicz.pl)
- LinkedIn: [linkedin.com/in/kamil-monicz](https://www.linkedin.com/in/kamil-monicz/)

### License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).

You can find the full text of the license in the repository at [LICENSE](https://github.com/Zaczero/teodle/blob/main/LICENSE).
