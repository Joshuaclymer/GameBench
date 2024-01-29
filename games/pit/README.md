# pit

This is a game engine for the Pit commodity-trading card game. The core code here is the game engine, which approximates the rules and gameplay of the card game. The idea is for you/anyone to write players and pit them against each other.

Note: the code appears to be functional but I haven't done comprehensive testing. Please let me know if you find issues and/or submit a fix. Thanks!

**There are two version of the game engine:**

## Synchronous version

- pit/sync/gameengine.py
- game engine runs a single game loop, fetching & processing player actions one at a time

## Async version

- pit/synca/gameengine.py
- players are spawned as processes, each with its own pipe and queue for communication back to the game engine
- my current sample/debugging players (SimplePlayer) are _extremely_ inefficient, taking several minutes (and hundreds of thousands of decisions) to complete a single game to 500

# links

- [Pit Wikipedia page](<http://en.wikipedia.org/wiki/Pit_(game)>)
- [Rules](http://www.howdoyouplayit.com/pit-card-game-rules/) (bull & bear variant used here)
- [Boardgame Geek page](http://boardgamegeek.com/boardgame/140/pit)
