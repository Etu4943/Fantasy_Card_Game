# Fantasy_Card_Game
#### Video Demo:  <URL HERE>
#### Description:
Here is my final project for CS50. 
Ther is this card game called *Fantasy* that we love with my partner, so I decided to make it playbale online.
This app is made with Flask. I loved what I learned about Flask during CS50. It kind of remembered me of my first "Hello world", when I first started learning dev some years ago, where I discoverd something totally new. I knew I could do something big with that.
The project is basically based on the use of sockets.

#### Disclaimer :
This game is based on a real card game called "Fantasy", which belongs to [Asmodee](https://www.asmodee.fr/). All the assets related to the cards are all scanned card from the game that I own. 

I do not own any intellectual property, rules, idea or assets from this game.

#### Where to play :
You can play this game anytime, at the latest version, here : https://fantasy.cpotier.be/

The game is **translated** ! For now it's available in French and English. But as it's just a json file, it could be translated in any language :)

#### Login
First, there is a login / register section. This is related to a sql3 databse. For now, it's on the app folder. But I'll host it on a dedicated server.
The passwords are hashed with the werkzeug security library.

#### 4 Pages
| Page  | Use |
|-------|-----|
| Profile | Here, you can change your avatar, your name, and your email address  |
| Join    | That's the 'main' page, where you can create a room or join a friend to play with  |
| Rules  | A page dedicated to explain every card ability  |
| Scoreboard  | The page where you can see the history of every game that has been played |

#### How to play ?
First, you draw a card. Then you play one on your board and its ability is triggered (If possible, otherwise nothing happens).
(For example, you can't reactivate on of the card on your board if you have none)
Then it's the enemy's turn.
The game stops when a player doesn't have any card left and if the deck is empty. You win the game by having the most cards on your board.

#### Screenshots
<img width="1280" height="1400" alt="image" src="https://github.com/user-attachments/assets/c981d638-8df0-473b-a894-7a44528ee2f8" />
<img width="1280" height="1400" alt="image" src="https://github.com/user-attachments/assets/f000e809-59af-422b-b717-e01714273fab" />




#### What about AI ?
To be honest, I've always been against the use of AI since chatGPT blew up. I saw people use it as their own brain, that was disturbing. That said, I had to admit that it's a really usefull tool if used the right way. 
So, since I wanted to create the game, the rules, the database, the behavior and so, AI "helped" me make it look good on screen. Clearly, Claude coded all the CSS I needed so I could focus on the thing I wanted to create.
Also, I figured out that AI could take picture on input and output cropped, and tilted version. So it fixed my crappy card's scan as well ! 

#### What's left to do ?
- If you scroll through my code, you can see that there is a card type I didn't implemented : The *fee*. 
It's supposed to cancel an ability while it's being played. I haven't figure out how to do so yet. 
The way I implemented the game is turn-based, and I try several things to "simulate" such as playing fee after the enemy. But that couldn't work fairly.
- Also, I'd like to implement HTML5 so I could play the cards like a real card game like hearthstone ! But that will come later.
- While recording the video demo, I found out that I can import an avatar, but i can't remove it. That's on my to-do list as well.
